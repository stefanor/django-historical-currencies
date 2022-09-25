from iso4217 import Currency


def iter_choices(exclude_special=True):
    """Iterator that produces a list of (unsorted) currency choices"""
    for currency in Currency:
        # Generally X currencies aren't currencies (except the ones that are)
        if (
            exclude_special
            and currency.code.startswith("X")
            and currency.code not in ("XAF", "XCD", "XOF", "XPF")
        ):
            continue

        yield (
            currency.code,
            f"{currency.code} ({currency.currency_name})",
        )


def currency_choices(**kwargs):
    """A list of CURRENCY: Descriptive Name for use in Django choices"""
    return sorted(list(iter_choices(**kwargs)))
