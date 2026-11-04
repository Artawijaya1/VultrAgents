-- ProcureGuard AI - MySQL 8.x schema (DEMO ONLY; no actual ERP integration).
-- All monetary values are DECIMAL, never FLOAT. Execute on a new database.
CREATE DATABASE IF NOT EXISTS procureguard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE procureguard;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(190) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('buyer','finance','auditor','approver','admin') NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS suppliers (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  supplier_code VARCHAR(40) NOT NULL UNIQUE,
  supplier_name VARCHAR(160) NOT NULL,
  status ENUM('active','inactive','suspended') NOT NULL DEFAULT 'active',
  verified_bank_fingerprint CHAR(64) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(40) NOT NULL UNIQUE,
  product_name VARCHAR(160) NOT NULL,
  unit VARCHAR(20) NOT NULL DEFAULT 'unit'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contracts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  supplier_id BIGINT NOT NULL,
  contract_number VARCHAR(50) NOT NULL UNIQUE,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  max_unit_price DECIMAL(18,2) NULL,
  currency CHAR(3) NOT NULL DEFAULT 'IDR',
  status ENUM('active','expired','cancelled') NOT NULL DEFAULT 'active',
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS purchase_orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  po_number VARCHAR(50) NOT NULL UNIQUE,
  supplier_id BIGINT NOT NULL,
  buyer_id BIGINT NOT NULL,
  contract_id BIGINT NULL,
  order_date DATE NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'IDR',
  status ENUM('draft','submitted','approved','part_received','closed','cancelled') NOT NULL DEFAULT 'draft',
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
  FOREIGN KEY (buyer_id) REFERENCES users(id),
  FOREIGN KEY (contract_id) REFERENCES contracts(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS purchase_order_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  purchase_order_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity DECIMAL(18,3) NOT NULL,
  unit_price DECIMAL(18,2) NOT NULL,
  expected_delivery_date DATE NULL,
  FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  CHECK (quantity > 0),
  CHECK (unit_price >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS invoices (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  supplier_id BIGINT NOT NULL,
  purchase_order_id BIGINT NULL,
  invoice_number VARCHAR(80) NOT NULL,
  invoice_date DATE NOT NULL,
  total_amount DECIMAL(18,2) NOT NULL,
  payment_bank_fingerprint CHAR(64) NULL,
  status ENUM('received','review','approved','paid','rejected') NOT NULL DEFAULT 'received',
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
  FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
  INDEX ix_invoice_supplier_number (supplier_id, invoice_number),
  INDEX ix_invoice_date (invoice_date),
  CHECK (total_amount >= 0)
) ENGINE=InnoDB;
-- Invoice number is NOT UNIQUE here so duplicate-import scenarios can be tested and flagged.
-- Production ingestion should prevent duplicate payment while retaining duplicate submissions as evidence.

CREATE TABLE IF NOT EXISTS invoice_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  invoice_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity DECIMAL(18,3) NOT NULL,
  unit_price DECIMAL(18,2) NOT NULL,
  FOREIGN KEY (invoice_id) REFERENCES invoices(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS supplier_bank_changes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  supplier_id BIGINT NOT NULL,
  old_bank_fingerprint CHAR(64) NULL,
  proposed_bank_fingerprint CHAR(64) NOT NULL,
  independently_verified BOOLEAN NOT NULL DEFAULT FALSE,
  verified_by BIGINT NULL,
  requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  verified_at TIMESTAMP NULL,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
  FOREIGN KEY (verified_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS negotiation_sessions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  purchase_order_id BIGINT NOT NULL,
  created_by BIGINT NOT NULL,
  status ENUM('draft','review','approved','closed') NOT NULL DEFAULT 'draft',
  objective TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS negotiation_offers (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  session_id BIGINT NOT NULL,
  round_number INT NOT NULL,
  party ENUM('buyer','supplier') NOT NULL,
  quantity DECIMAL(18,3) NOT NULL,
  offered_unit_price DECIMAL(18,2) NOT NULL,
  proposed_delivery_date DATE NULL,
  message_draft TEXT NULL,
  approval_status ENUM('draft','pending','approved','rejected') NOT NULL DEFAULT 'draft',
  FOREIGN KEY (session_id) REFERENCES negotiation_sessions(id),
  INDEX ix_offer_round (session_id, round_number)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fraud_alerts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  supplier_id BIGINT NULL,
  invoice_id BIGINT NULL,
  purchase_order_id BIGINT NULL,
  rule_code VARCHAR(70) NOT NULL,
  severity ENUM('low','medium','high','critical') NOT NULL,
  status ENUM('open','investigating','resolved','false_positive') NOT NULL DEFAULT 'open',
  explanation TEXT NOT NULL,
  evidence JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
  FOREIGN KEY (invoice_id) REFERENCES invoices(id),
  FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
  INDEX ix_alert_status (status, severity, created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fraud_reviews (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alert_id BIGINT NOT NULL,
  reviewer_id BIGINT NOT NULL,
  outcome ENUM('needs_more_evidence','legitimate','confirmed_violation','inconclusive') NOT NULL,
  reviewer_notes TEXT NULL,
  reviewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (alert_id) REFERENCES fraud_alerts(id),
  FOREIGN KEY (reviewer_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS approval_requests (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  requested_by BIGINT NOT NULL,
  decided_by BIGINT NULL,
  entity_type VARCHAR(40) NOT NULL,
  entity_id BIGINT NOT NULL,
  action_type VARCHAR(60) NOT NULL,
  status ENUM('pending','approved','rejected','cancelled') NOT NULL DEFAULT 'pending',
  reason TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  decided_at TIMESTAMP NULL,
  FOREIGN KEY (requested_by) REFERENCES users(id),
  FOREIGN KEY (decided_by) REFERENCES users(id),
  CHECK (decided_by IS NULL OR decided_by <> requested_by)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  actor_id BIGINT NULL,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id VARCHAR(70) NOT NULL,
  request_trace_id VARCHAR(100) NULL,
  event_payload JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (actor_id) REFERENCES users(id),
  INDEX ix_audit_entity (entity_type, entity_id, created_at)
) ENGINE=InnoDB;
