from setuptools import setup, find_packages

setup(
    name="ai-trader-tools",
    version="0.1.0",
    description="Open-source tool library for AI/LLM-driven trading agents (crypto + MT5, TA, sentiment, risk).",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "ccxt>=4.0.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
        "vaderSentiment>=3.3.2",
    ],
    extras_require={"mt5": ["MetaTrader5>=5.0.45"]},
    python_requires=">=3.9",
)
