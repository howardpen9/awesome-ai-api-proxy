"""Group ratios, billing expressions, placeholders, top-up, inactive skip."""

from fetchers._new_api import (
    choose_pricing_group,
    is_unset_model_ratio,
    parse_billing_expr,
)
from scripts.build_prices import (
    effective_price_usd,
    records_for_current_build,
    topup_multiplier,
)
from scripts.scrape import include_in_scrape

GPT54_EXPR = (
    'len <= 271999 ? tier("≤ 271999", p * 2.5 + c * 15 + cr * 0.25)'
    ' : tier("> 271999", p * 5 + c * 22.5 + cr * 0.5)'
)
OPUS5_EXPR = 'tier("base", p * 5 + c * 25 + cr * 0.5 + cc * 6.25 + cc1h * 10)'


def test_explicit_default_group_filters_and_uses_its_ratio():
    ratios = {"default": 1.0, "vip": 4.17, "sssvip": 0.37}
    in_default = {"enable_groups": ["default", "vip", "sssvip"]}
    choice = choose_pricing_group(in_default, ratios, group="default", per_enable_group=False)
    assert choice is not None
    assert choice.name == "default"
    assert choice.ratio == 1.0
    # Cheaper and more expensive groups exist; default is what a default user pays.
    assert choice.ratio_max == 4.17

    vip_only = {"enable_groups": ["vip"]}
    assert choose_pricing_group(vip_only, ratios, group="default", per_enable_group=False) is None


def test_sole_enable_group_uses_that_ratio_not_one():
    ratios = {"Claude": 0.68, "GPT": 0.68}
    choice = choose_pricing_group(
        {"enable_groups": ["Claude"]},
        ratios,
        group=None,
        per_enable_group=True,
    )
    assert choice is not None
    assert choice.name == "Claude"
    assert choice.ratio == 0.68


def test_no_default_uses_cheapest_positive_ratio_not_free_or_list():
    ratios = {
        "free-pool": 0.0,
        "a-cheap": 0.2235,
        "b-mid": 0.447,
        "enterprise": 0.9,
    }
    model = {"enable_groups": ["free-pool", "b-mid", "a-cheap", "enterprise"]}
    choice = choose_pricing_group(model, ratios, group=None, per_enable_group=False)
    assert choice is not None
    assert choice.name == "a-cheap"
    assert choice.ratio == 0.2235
    assert choice.ratio_max == 0.9


def test_missing_group_metadata_stays_at_list_ratio():
    choice = choose_pricing_group({}, {}, group=None, per_enable_group=False)
    assert choice is not None
    assert choice.name is None
    assert choice.ratio == 1.0


def test_billing_expr_short_context_not_legacy_75():
    parsed = parse_billing_expr(GPT54_EXPR)
    assert parsed is not None
    assert parsed.input_per_1m == 2.5
    assert parsed.output_per_1m == 15
    assert parsed.cache_read_per_1m == 0.25
    assert parsed.tier == "≤ 271999"
    # The long-context branch is $5 / $22.50 and must not win.
    assert parsed.input_per_1m != 5

    opus = parse_billing_expr(OPUS5_EXPR)
    assert opus is not None
    assert opus.input_per_1m == 5
    assert opus.output_per_1m == 25
    # cc * 6.25 must not be read as output `c`.
    assert opus.output_per_1m != 6.25


def test_fixed_call_price():
    parsed = parse_billing_expr('tier("base", fixed(0.05))')
    assert parsed is not None
    assert parsed.fixed_price == 0.05
    assert parsed.input_per_1m is None


def test_unset_ratio_is_37_5_only():
    assert is_unset_model_ratio(37.5)
    assert not is_unset_model_ratio(1.5)
    assert not is_unset_model_ratio(0.375)


def test_uiuiapi_topup_turns_quota_usd_into_effective_usd():
    rate = {"amount": 3.37, "currency": "CNY", "fx_per_usd": 6.79}
    # gpt-5.4 short-context input, default group ratio 1.
    assert effective_price_usd(2.5, rate) == round(2.5 * 3.37 / 6.79, 6)
    assert topup_multiplier({"amount": 6.8, "fx_per_usd": 6.8}) == 1
    assert effective_price_usd(3.0, None) is None
    assert effective_price_usd(3.0, {"amount": 3.37}) is None


def test_build_drops_placeholders_and_inactive_fetchers():
    rows = [
        {"provider_id": "uiuiapi", "price_usd": 75.0, "price_placeholder": True},
        {"provider_id": "uiuiapi", "price_usd": 2.5},
        {"provider_id": "bltcy", "price_usd": 2.5},
        {"provider_id": "openrouter", "price_usd": 2.5},
    ]
    kept, excluded = records_for_current_build(rows, {"bltcy"})
    assert excluded == 1
    assert [r["provider_id"] for r in kept] == ["uiuiapi", "openrouter"]
    assert kept[0]["price_usd"] == 2.5


def test_inactive_provider_is_not_scraped():
    assert include_in_scrape({"status": "active", "pricing": {"fetcher": "uiuiapi"}})
    assert not include_in_scrape({"status": "inactive", "pricing": {"fetcher": "bltcy"}})
    assert not include_in_scrape({"status": "active", "pricing": {}})
