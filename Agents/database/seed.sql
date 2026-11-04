USE procureguard;
-- Identitas, kontak dan harga berikut hanyalah data ilustratif.
INSERT INTO users (id, email, password_hash, role) VALUES
(1,'buyer.demo@example.invalid','DISABLED_NO_LOGIN','buyer'),
(2,'reviewer.demo@example.invalid','DISABLED_NO_LOGIN','approver'),
(3,'audit.demo@example.invalid','DISABLED_NO_LOGIN','auditor');
INSERT INTO suppliers (id, supplier_code, supplier_name, status) VALUES
(1,'SUP-001','PT Sinar Logistik','active'),
(2,'SUP-002','CV Mitra Niaga','active');
INSERT INTO products (id, sku, product_name, unit) VALUES
(101,'BRG-101','Peralatan kantor','unit'),
(102,'BRG-102','Perlengkapan gudang','unit');
INSERT INTO contracts (id, supplier_id, contract_number, start_date, end_date, max_unit_price) VALUES
(1,1,'KON-001','2026-01-01','2026-12-31',155000);
INSERT INTO purchase_orders (id, po_number, supplier_id, buyer_id, contract_id, order_date) VALUES
(1,'PO-001',1,1,1,'2026-10-28');
INSERT INTO purchase_order_items (id, purchase_order_id, product_id, quantity, unit_price, expected_delivery_date) VALUES
(1,1,101,100,150000,'2026-11-10');
INSERT INTO invoices (id, supplier_id, purchase_order_id, invoice_number, invoice_date, total_amount) VALUES
(1,1,1,'INV-100','2026-10-30',15000000),
(2,1,1,'INV-100','2026-10-31',15000000);
INSERT INTO approval_requests (id, requested_by, entity_type, entity_id, action_type, status)
VALUES (1,1,'negotiation_offer',1,'send_supplier_proposal','pending');
