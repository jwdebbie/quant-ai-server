-- V7: 수집 실패 내역 테이블
CREATE TABLE IF NOT EXISTS collection_failures (
    id          BIGSERIAL    PRIMARY KEY,
    stock_code  VARCHAR(10)  NOT NULL,
    reason      TEXT         NOT NULL,
    failed_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collection_failures_stock_code ON collection_failures (stock_code);
CREATE INDEX IF NOT EXISTS idx_collection_failures_failed_at  ON collection_failures (failed_at);
