# Binomial Option Pricing (Python)

This repository implements a binomial tree option pricer in pure Python. Use
`binomial_pricing.py` to value European or American call/put options with
configurable dividend yield and tree depth.

## Quick start

```bash
python binomial_pricing.py
```

The sample in `__main__` prints prices for a European and American call using
100 time steps. For programmatic use, import `price_option` with the
`BinomialParameters` dataclass or use `price_option_simplified` for a
lightweight interface.
