FROM python:3.11-slim AS talib-builder

# TA-Lib's Python wheel needs the TA-Lib C library, which isn't packaged for
# Debian, so build it from source once in its own stage.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/talib
RUN wget -q https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install DESTDIR=/talib-install


FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/whchien/ai-trader"
LABEL org.opencontainers.image.description="Backtrader-powered backtesting framework for algorithmic trading"

# Runtime libs needed by lxml/matplotlib; TA-Lib C library copied from the
# builder stage above instead of recompiling it here.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=talib-builder /talib-install/usr /usr
RUN ldconfig

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY ai_trader ./ai_trader
COPY config ./config
COPY data ./data
COPY README.md ./

RUN pip install --no-cache-dir .

# Persist fetched market data / SQLite cache outside the image.
VOLUME ["/app/data", "/app/config"]

ENTRYPOINT ["ai-trader"]
CMD ["--help"]
