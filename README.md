# Binomial Option Pricing (Python)

This repository implements a binomial tree option pricer in pure Python. Use
`binomial_pricing.py` to value European or American call/put options with
configurable dividend yield and tree depth.

`monte_carlo_pricing.py` adds a Monte Carlo pricer that accepts a
user-supplied payoff expression using ``S`` as the terminal price symbol (for
example, ``max(S - 100, 0)`` for a vanilla call). A lightweight Flask web UI
and JSON API are provided in `web_app.py` for interactive pricing.

## Quick start

```bash
python binomial_pricing.py
```

Run the Monte Carlo pricer with a custom payoff expression:

```bash
python monte_carlo_pricing.py --payoff "max(S - 100, 0)" --spot 100 --maturity 1 --rate 0.05 --volatility 0.2 --simulations 5000
```

The sample in `__main__` prints prices for a European and American call using
100 time steps. For programmatic use, import `price_option` with the
`BinomialParameters` dataclass or use `price_option_simplified` for a
lightweight interface.

## Web option calculator

Launch the Flask server to access a form-based Monte Carlo pricer and a JSON API:

```bash
pip install flask
python web_app.py
```

Then open http://127.0.0.1:8000 to enter pricing inputs and get results in the
browser. The page accepts a payoff expression written with ``S`` for the
terminal price and shows any validation errors inline.

To price programmatically via HTTP, send JSON to `/api/price`:

```bash
curl -X POST http://127.0.0.1:8000/api/price \
  -H "Content-Type: application/json" \
  -d '{"spot": 100, "maturity": 1, "rate": 0.05, "volatility": 0.2, "simulations": 50000, "payoff": "max(S - 100, 0)"}'
```

The response includes the estimated price or an error message if inputs are
invalid.
