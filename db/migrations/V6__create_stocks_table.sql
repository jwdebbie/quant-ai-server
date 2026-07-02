-- V6: stocks 마스터 테이블 생성 및 초기 데이터 삽입
-- 종목코드 기준 마스터 테이블. stock_prices, news_articles 등의 FK 기준.

CREATE TABLE IF NOT EXISTS stocks (
    id         BIGSERIAL    PRIMARY KEY,
    code       VARCHAR(10)  NOT NULL UNIQUE,   -- 종목코드 (예: 005930)
    name       VARCHAR(100) NOT NULL,           -- 종목명 (예: 삼성전자)
    market     VARCHAR(10)  NOT NULL DEFAULT 'KRX',
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 초기 종목 10개 삽입 (중복 시 무시)
INSERT INTO stocks (code, name, market) VALUES
    ('005930', '삼성전자',       'KRX'),
    ('000660', 'SK하이닉스',     'KRX'),
    ('402340', 'SK스퀘어',       'KRX'),
    ('207940', '삼성바이오로직스','KRX'),
    ('005380', '현대차',         'KRX'),
    ('373220', 'LG에너지솔루션', 'KRX'),
    ('032830', '삼성생명',       'KRX'),
    ('028260', '삼성물산',       'KRX'),
    ('329180', 'HD현대중공업',   'KRX'),
    ('000270', '기아',           'KRX')
ON CONFLICT (code) DO NOTHING;
