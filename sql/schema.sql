--
-- PostgreSQL database dump
--

\restrict 2N6V4TDdqjoMCZjbSBDwV8S7Yhf6eDLOXWGwBHAbp3q97iR0tICPxdcnMVqXMfY

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    category_id bigint NOT NULL,
    category_name character varying(100) NOT NULL,
    department character varying(100) NOT NULL
);


--
-- Name: categories_category_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.categories_category_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categories_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.categories_category_id_seq OWNED BY public.categories.category_id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    customer_id bigint NOT NULL,
    customer_segment character varying(50) NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    country character varying(100) DEFAULT 'India'::character varying NOT NULL,
    signup_date date NOT NULL
);


--
-- Name: customers_customer_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.customers_customer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_customer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.customers_customer_id_seq OWNED BY public.customers.customer_id;


--
-- Name: inventory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory (
    inventory_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    product_id bigint NOT NULL,
    snapshot_date date NOT NULL,
    opening_stock integer DEFAULT 0 NOT NULL,
    received_quantity integer DEFAULT 0 NOT NULL,
    sold_quantity integer DEFAULT 0 NOT NULL,
    returned_quantity integer DEFAULT 0 NOT NULL,
    adjustment_quantity integer DEFAULT 0 NOT NULL,
    closing_stock integer DEFAULT 0 NOT NULL,
    reserved_quantity integer DEFAULT 0 NOT NULL,
    CONSTRAINT chk_inventory_closing CHECK ((closing_stock >= 0)),
    CONSTRAINT chk_inventory_opening CHECK ((opening_stock >= 0)),
    CONSTRAINT chk_inventory_received CHECK ((received_quantity >= 0)),
    CONSTRAINT chk_inventory_reserved CHECK ((reserved_quantity >= 0)),
    CONSTRAINT chk_inventory_returned CHECK ((returned_quantity >= 0)),
    CONSTRAINT chk_inventory_sold CHECK ((sold_quantity >= 0))
);


--
-- Name: inventory_inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_inventory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_inventory_id_seq OWNED BY public.inventory.inventory_id;


--
-- Name: inventory_movements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inventory_movements (
    movement_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    product_id bigint NOT NULL,
    movement_type character varying(50) NOT NULL,
    quantity integer NOT NULL,
    movement_date timestamp without time zone NOT NULL,
    reference_id character varying(100),
    CONSTRAINT chk_movement_quantity CHECK ((quantity > 0)),
    CONSTRAINT chk_movement_type CHECK (((movement_type)::text = ANY ((ARRAY['PURCHASE_RECEIPT'::character varying, 'SALE'::character varying, 'RETURN'::character varying, 'TRANSFER_IN'::character varying, 'TRANSFER_OUT'::character varying, 'DAMAGE'::character varying, 'ADJUSTMENT'::character varying])::text[])))
);


--
-- Name: inventory_movements_movement_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inventory_movements_movement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inventory_movements_movement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inventory_movements_movement_id_seq OWNED BY public.inventory_movements.movement_id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.order_items (
    order_item_id bigint NOT NULL,
    order_id bigint NOT NULL,
    product_id bigint NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(12,2) NOT NULL,
    discount numeric(12,2) DEFAULT 0 NOT NULL,
    total_amount numeric(14,2) NOT NULL,
    CONSTRAINT chk_order_item_discount CHECK ((discount >= (0)::numeric)),
    CONSTRAINT chk_order_item_price CHECK ((unit_price >= (0)::numeric)),
    CONSTRAINT chk_order_item_quantity CHECK ((quantity > 0)),
    CONSTRAINT chk_order_item_total CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: order_items_order_item_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.order_items_order_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_items_order_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.order_items_order_item_id_seq OWNED BY public.order_items.order_item_id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orders (
    order_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    warehouse_id bigint,
    order_date timestamp without time zone NOT NULL,
    order_status character varying(30) NOT NULL,
    payment_method character varying(50),
    order_value numeric(14,2) DEFAULT 0 NOT NULL,
    shipping_city character varying(100),
    shipping_state character varying(100),
    promised_delivery_date timestamp without time zone,
    actual_delivery_date timestamp without time zone,
    CONSTRAINT chk_order_status CHECK (((order_status)::text = ANY ((ARRAY['PLACED'::character varying, 'CONFIRMED'::character varying, 'PROCESSING'::character varying, 'SHIPPED'::character varying, 'DELIVERED'::character varying, 'CANCELLED'::character varying, 'RETURNED'::character varying])::text[]))),
    CONSTRAINT chk_order_value CHECK ((order_value >= (0)::numeric))
);


--
-- Name: orders_order_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.orders_order_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_order_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.orders_order_id_seq OWNED BY public.orders.order_id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    product_id bigint NOT NULL,
    sku character varying(50) NOT NULL,
    product_name character varying(255) NOT NULL,
    category_id bigint NOT NULL,
    brand character varying(100),
    unit_cost numeric(12,2) NOT NULL,
    selling_price numeric(12,2) NOT NULL,
    weight_kg numeric(10,2),
    reorder_point integer DEFAULT 0 NOT NULL,
    safety_stock integer DEFAULT 0 NOT NULL,
    supplier_id bigint,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_product_cost CHECK ((unit_cost >= (0)::numeric)),
    CONSTRAINT chk_product_price CHECK ((selling_price >= (0)::numeric)),
    CONSTRAINT chk_product_weight CHECK (((weight_kg IS NULL) OR (weight_kg >= (0)::numeric))),
    CONSTRAINT chk_reorder_point CHECK ((reorder_point >= 0)),
    CONSTRAINT chk_safety_stock CHECK ((safety_stock >= 0))
);


--
-- Name: products_product_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.products_product_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_product_id_seq OWNED BY public.products.product_id;


--
-- Name: purchase_order_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.purchase_order_items (
    po_item_id bigint NOT NULL,
    po_id bigint NOT NULL,
    product_id bigint NOT NULL,
    ordered_quantity integer NOT NULL,
    received_quantity integer DEFAULT 0 NOT NULL,
    unit_cost numeric(12,2) NOT NULL,
    CONSTRAINT chk_ordered_quantity CHECK ((ordered_quantity > 0)),
    CONSTRAINT chk_po_unit_cost CHECK ((unit_cost >= (0)::numeric)),
    CONSTRAINT chk_received_quantity CHECK (((received_quantity >= 0) AND (received_quantity <= ordered_quantity)))
);


--
-- Name: purchase_order_items_po_item_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.purchase_order_items_po_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: purchase_order_items_po_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_order_items_po_item_id_seq OWNED BY public.purchase_order_items.po_item_id;


--
-- Name: purchase_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.purchase_orders (
    po_id bigint NOT NULL,
    supplier_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    po_date timestamp without time zone NOT NULL,
    expected_delivery_date timestamp without time zone NOT NULL,
    actual_delivery_date timestamp without time zone,
    po_status character varying(30) NOT NULL,
    CONSTRAINT chk_po_status CHECK (((po_status)::text = ANY ((ARRAY['CREATED'::character varying, 'CONFIRMED'::character varying, 'PARTIALLY_RECEIVED'::character varying, 'RECEIVED'::character varying, 'CANCELLED'::character varying])::text[])))
);


--
-- Name: purchase_orders_po_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.purchase_orders_po_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: purchase_orders_po_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.purchase_orders_po_id_seq OWNED BY public.purchase_orders.po_id;


--
-- Name: returns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.returns (
    return_id bigint NOT NULL,
    order_id bigint NOT NULL,
    order_item_id bigint NOT NULL,
    product_id bigint NOT NULL,
    return_date timestamp without time zone NOT NULL,
    return_quantity integer NOT NULL,
    return_reason character varying(100) NOT NULL,
    refund_amount numeric(14,2) NOT NULL,
    return_status character varying(50) NOT NULL,
    CONSTRAINT chk_refund_amount CHECK ((refund_amount >= (0)::numeric)),
    CONSTRAINT chk_return_quantity CHECK ((return_quantity > 0)),
    CONSTRAINT chk_return_reason CHECK (((return_reason)::text = ANY ((ARRAY['DAMAGED'::character varying, 'DEFECTIVE'::character varying, 'WRONG_ITEM'::character varying, 'SIZE_ISSUE'::character varying, 'CUSTOMER_CHANGED_MIND'::character varying, 'LATE_DELIVERY'::character varying, 'NOT_AS_EXPECTED'::character varying])::text[])))
);


--
-- Name: returns_return_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.returns_return_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: returns_return_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.returns_return_id_seq OWNED BY public.returns.return_id;


--
-- Name: shipments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipments (
    shipment_id bigint NOT NULL,
    order_id bigint NOT NULL,
    warehouse_id bigint NOT NULL,
    carrier character varying(100),
    shipment_status character varying(50) NOT NULL,
    shipped_at timestamp without time zone,
    estimated_delivery_date timestamp without time zone,
    actual_delivery_date timestamp without time zone,
    shipping_cost numeric(12,2) DEFAULT 0 NOT NULL,
    CONSTRAINT chk_shipment_status CHECK (((shipment_status)::text = ANY ((ARRAY['CREATED'::character varying, 'PACKED'::character varying, 'SHIPPED'::character varying, 'IN_TRANSIT'::character varying, 'OUT_FOR_DELIVERY'::character varying, 'DELIVERED'::character varying, 'LOST'::character varying, 'CANCELLED'::character varying])::text[]))),
    CONSTRAINT chk_shipping_cost CHECK ((shipping_cost >= (0)::numeric))
);


--
-- Name: shipments_shipment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shipments_shipment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shipments_shipment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shipments_shipment_id_seq OWNED BY public.shipments.shipment_id;


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.suppliers (
    supplier_id bigint NOT NULL,
    supplier_name character varying(255) NOT NULL,
    country character varying(100) NOT NULL,
    state character varying(100),
    city character varying(100),
    supplier_type character varying(100),
    rating numeric(3,2),
    default_lead_time_days integer NOT NULL,
    payment_terms character varying(50),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_supplier_lead_time CHECK ((default_lead_time_days >= 0)),
    CONSTRAINT chk_supplier_rating CHECK (((rating IS NULL) OR ((rating >= (0)::numeric) AND (rating <= (5)::numeric))))
);


--
-- Name: suppliers_supplier_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.suppliers_supplier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: suppliers_supplier_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.suppliers_supplier_id_seq OWNED BY public.suppliers.supplier_id;


--
-- Name: warehouses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.warehouses (
    warehouse_id bigint NOT NULL,
    warehouse_name character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    country character varying(100) DEFAULT 'India'::character varying NOT NULL,
    warehouse_type character varying(50),
    capacity_units bigint NOT NULL,
    operating_cost_per_day numeric(12,2) NOT NULL,
    latitude numeric(9,6),
    longitude numeric(9,6),
    opened_at date,
    CONSTRAINT chk_operating_cost CHECK ((operating_cost_per_day >= (0)::numeric)),
    CONSTRAINT chk_warehouse_capacity CHECK ((capacity_units >= 0))
);


--
-- Name: warehouses_warehouse_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.warehouses_warehouse_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouses_warehouse_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.warehouses_warehouse_id_seq OWNED BY public.warehouses.warehouse_id;


--
-- Name: categories category_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories ALTER COLUMN category_id SET DEFAULT nextval('public.categories_category_id_seq'::regclass);


--
-- Name: customers customer_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers ALTER COLUMN customer_id SET DEFAULT nextval('public.customers_customer_id_seq'::regclass);


--
-- Name: inventory inventory_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory ALTER COLUMN inventory_id SET DEFAULT nextval('public.inventory_inventory_id_seq'::regclass);


--
-- Name: inventory_movements movement_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_movements ALTER COLUMN movement_id SET DEFAULT nextval('public.inventory_movements_movement_id_seq'::regclass);


--
-- Name: order_items order_item_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items ALTER COLUMN order_item_id SET DEFAULT nextval('public.order_items_order_item_id_seq'::regclass);


--
-- Name: orders order_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders ALTER COLUMN order_id SET DEFAULT nextval('public.orders_order_id_seq'::regclass);


--
-- Name: products product_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN product_id SET DEFAULT nextval('public.products_product_id_seq'::regclass);


--
-- Name: purchase_order_items po_item_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items ALTER COLUMN po_item_id SET DEFAULT nextval('public.purchase_order_items_po_item_id_seq'::regclass);


--
-- Name: purchase_orders po_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders ALTER COLUMN po_id SET DEFAULT nextval('public.purchase_orders_po_id_seq'::regclass);


--
-- Name: returns return_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.returns ALTER COLUMN return_id SET DEFAULT nextval('public.returns_return_id_seq'::regclass);


--
-- Name: shipments shipment_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments ALTER COLUMN shipment_id SET DEFAULT nextval('public.shipments_shipment_id_seq'::regclass);


--
-- Name: suppliers supplier_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers ALTER COLUMN supplier_id SET DEFAULT nextval('public.suppliers_supplier_id_seq'::regclass);


--
-- Name: warehouses warehouse_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouses ALTER COLUMN warehouse_id SET DEFAULT nextval('public.warehouses_warehouse_id_seq'::regclass);


--
-- Name: categories categories_category_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_category_name_key UNIQUE (category_name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (category_id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- Name: inventory_movements inventory_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT inventory_movements_pkey PRIMARY KEY (movement_id);


--
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (inventory_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (order_item_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (order_id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: products products_sku_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_sku_key UNIQUE (sku);


--
-- Name: purchase_order_items purchase_order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT purchase_order_items_pkey PRIMARY KEY (po_item_id);


--
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (po_id);


--
-- Name: returns returns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.returns
    ADD CONSTRAINT returns_pkey PRIMARY KEY (return_id);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (shipment_id);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (supplier_id);


--
-- Name: inventory uq_inventory_snapshot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT uq_inventory_snapshot UNIQUE (warehouse_id, product_id, snapshot_date);


--
-- Name: warehouses warehouses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.warehouses
    ADD CONSTRAINT warehouses_pkey PRIMARY KEY (warehouse_id);


--
-- Name: inventory fk_inventory_product; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: inventory fk_inventory_warehouse; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT fk_inventory_warehouse FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(warehouse_id);


--
-- Name: inventory_movements fk_movement_product; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT fk_movement_product FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: inventory_movements fk_movement_warehouse; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inventory_movements
    ADD CONSTRAINT fk_movement_warehouse FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(warehouse_id);


--
-- Name: orders fk_order_customer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: order_items fk_order_item_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES public.orders(order_id) ON DELETE CASCADE;


--
-- Name: order_items fk_order_item_product; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: orders fk_order_warehouse; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT fk_order_warehouse FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(warehouse_id);


--
-- Name: purchase_order_items fk_po_item_po; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT fk_po_item_po FOREIGN KEY (po_id) REFERENCES public.purchase_orders(po_id) ON DELETE CASCADE;


--
-- Name: purchase_order_items fk_po_item_product; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT fk_po_item_product FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: purchase_orders fk_po_supplier; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id) REFERENCES public.suppliers(supplier_id);


--
-- Name: purchase_orders fk_po_warehouse; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT fk_po_warehouse FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(warehouse_id);


--
-- Name: products fk_product_category; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES public.categories(category_id);


--
-- Name: products fk_product_supplier; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT fk_product_supplier FOREIGN KEY (supplier_id) REFERENCES public.suppliers(supplier_id);


--
-- Name: returns fk_return_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.returns
    ADD CONSTRAINT fk_return_order FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- Name: returns fk_return_order_item; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.returns
    ADD CONSTRAINT fk_return_order_item FOREIGN KEY (order_item_id) REFERENCES public.order_items(order_item_id);


--
-- Name: returns fk_return_product; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.returns
    ADD CONSTRAINT fk_return_product FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: shipments fk_shipment_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT fk_shipment_order FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- Name: shipments fk_shipment_warehouse; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT fk_shipment_warehouse FOREIGN KEY (warehouse_id) REFERENCES public.warehouses(warehouse_id);


--
-- PostgreSQL database dump complete
--

\unrestrict 2N6V4TDdqjoMCZjbSBDwV8S7Yhf6eDLOXWGwBHAbp3q97iR0tICPxdcnMVqXMfY

