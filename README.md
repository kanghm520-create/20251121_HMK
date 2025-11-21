# Binomial Option Pricing (Python)

This repository implements a binomial tree option pricer in pure Python. Use
`binomial_pricing.py` to value European or American call/put options with
configurable dividend yield and tree depth.

`monte_carlo_pricing.py` adds a Monte Carlo pricer that accepts a
user-supplied payoff expression using ``S`` as the terminal price symbol (for
example, ``max(S - 100, 0)`` for a vanilla call).

## Quick start

```bash
python binomial_pricing.py
```

Run the Monte Carlo pricer with a custom payoff expression:

```bash
python monte_carlo_pricing.py --payoff "max(S - 100, 0)" --spot 100 --maturity 1 --rate 0.05 --volatility 0.2 --simulations 50000
```

The sample in `__main__` prints prices for a European and American call using
100 time steps. For programmatic use, import `price_option` with the
`BinomialParameters` dataclass or use `price_option_simplified` for a
lightweight interface.
