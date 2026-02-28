### Slide 1: TABLE - USERS (Django Auth)

| FIELD NAME  | DATA TYPE             | DESCRIPTION       |
| ----------- | --------------------- | ----------------- |
| id          | INTEGER (PRIMARY KEY) | PRIMARY KEY       |
| username    | STRING (UNIQUE)       | UNIQUE, NOT NULL  |
| email       | STRING                | NOT NULL          |
| password    | STRING                | NOT NULL          |
| first_name  | STRING                | NOT NULL          |
| last_name   | STRING                | NOT NULL          |
| is_staff    | BOOLEAN               | DEFAULT, NOT NULL |
| is_active   | BOOLEAN               | DEFAULT, NOT NULL |
| date_joined | DATETIME              | DEFAULT           |

---

### Slide 2: TABLE - USERPROFILE

| FIELD NAME    | DATA TYPE             | DESCRIPTION |
| ------------- | --------------------- | ----------- |
| id            | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id       | INTEGER (FOREIGN KEY) | NOT NULL    |
| profile_photo | IMAGE                 | NULL        |
| phone_number  | STRING                | NOT NULL    |

---

### Slide 3: TABLE - ADDRESS

| FIELD NAME   | DATA TYPE             | DESCRIPTION |
| ------------ | --------------------- | ----------- |
| id           | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id      | INTEGER (FOREIGN KEY) | NOT NULL    |
| full_name    | STRING                | NOT NULL    |
| phone        | STRING                | NOT NULL    |
| address_line | TEXT                  | NOT NULL    |
| city         | STRING                | NOT NULL    |
| state        | STRING                | NOT NULL    |
| postal_code  | STRING                | NOT NULL    |
| is_default   | BOOLEAN               | DEFAULT     |

---

### Slide 4: TABLE - USERMEASUREMENTS

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id    | INTEGER (FOREIGN KEY) | NOT NULL    |
| height_cm  | FLOAT                 | NOT NULL    |
| weight_kg  | FLOAT                 | NOT NULL    |
| gender     | STRING                | NOT NULL    |
| age        | INTEGER               | NOT NULL    |
| updated_at | DATETIME              | DEFAULT     |

---

### Slide 5: TABLE - USERPRODUCTINTERACTION

| FIELD NAME       | DATA TYPE             | DESCRIPTION |
| ---------------- | --------------------- | ----------- |
| id               | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id          | INTEGER (FOREIGN KEY) | NOT NULL    |
| product_id       | INTEGER (FOREIGN KEY) | NOT NULL    |
| interaction_type | STRING                | NOT NULL    |
| score            | INTEGER               | DEFAULT     |
| created_at       | DATETIME              | DEFAULT     |

---

### Slide 6: TABLE - FAQ

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| question   | STRING                | NOT NULL    |
| answer     | TEXT                  | NOT NULL    |
| category   | STRING                | NULL        |
| created_at | DATETIME              | DEFAULT     |
| updated_at | DATETIME              | DEFAULT     |

---

### Slide 7: TABLE - CART

| FIELD NAME  | DATA TYPE             | DESCRIPTION |
| ----------- | --------------------- | ----------- |
| id          | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id     | INTEGER (FOREIGN KEY) | NULL        |
| session_key | STRING                | NULL        |
| created_at  | DATETIME              | DEFAULT     |
| updated_at  | DATETIME              | DEFAULT     |

---

### Slide 8: TABLE - CARTITEM

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| cart_id    | INTEGER (FOREIGN KEY) | NOT NULL    |
| product_id | INTEGER (FOREIGN KEY) | NOT NULL    |
| size       | STRING                | NOT NULL    |
| color      | STRING                | NULL        |
| quantity   | INTEGER               | DEFAULT     |

---

### Slide 9: TABLE - CATEGORY

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| name       | STRING                | NOT NULL    |
| is_active  | BOOLEAN               | DEFAULT     |

---

### Slide 10: TABLE - PRODUCT

| FIELD NAME           | DATA TYPE             | DESCRIPTION |
| -------------------- | --------------------- | ----------- |
| id                   | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| category_id          | INTEGER (FOREIGN KEY) | NOT NULL    |
| name                 | STRING                | NOT NULL    |
| description          | TEXT                  | NOT NULL    |
| price                | DECIMAL               | NOT NULL    |
| stock                | INTEGER               | NOT NULL    |
| color                | STRING                | NULL        |
| tags                 | TEXT                  | NOT NULL    |
| is_dynamic_pricing   | BOOLEAN               | DEFAULT     |
| base_price           | DECIMAL               | NULL        |
| max_price            | DECIMAL               | NULL        |
| view_count           | INTEGER               | DEFAULT     |
| cart_add_count       | INTEGER               | DEFAULT     |
| units_sold           | INTEGER               | DEFAULT     |
| current_demand_score | INTEGER               | DEFAULT     |
| is_active            | BOOLEAN               | DEFAULT     |
| created_at           | DATETIME              | DEFAULT     |

---

### Slide 11: TABLE - PRODUCTIMAGE

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| product_id | INTEGER (FOREIGN KEY) | NOT NULL    |
| image      | IMAGE                 | NOT NULL    |

---

### Slide 12: TABLE - PRODUCTVARIANT

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| product_id | INTEGER (FOREIGN KEY) | NOT NULL    |
| size       | STRING                | NOT NULL    |
| stock      | INTEGER               | DEFAULT     |

---

### Slide 13: TABLE - COUPON

| FIELD NAME       | DATA TYPE             | DESCRIPTION      |
| ---------------- | --------------------- | ---------------- |
| id               | INTEGER (PRIMARY KEY) | PRIMARY KEY      |
| code             | STRING (UNIQUE)       | UNIQUE, NOT NULL |
| discount_type    | STRING                | NOT NULL         |
| discount_value   | DECIMAL               | NOT NULL         |
| min_order_amount | DECIMAL               | DEFAULT          |
| expiry_date      | DATE                  | NOT NULL         |
| active           | BOOLEAN               | DEFAULT          |
| created_at       | DATETIME              | DEFAULT          |

---

### Slide 14: TABLE - ORDER

| FIELD NAME      | DATA TYPE             | DESCRIPTION |
| --------------- | --------------------- | ----------- |
| id              | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id         | INTEGER (FOREIGN KEY) | NOT NULL    |
| address_id      | INTEGER (FOREIGN KEY) | NULL        |
| total_amount    | DECIMAL               | NOT NULL    |
| coupon_id       | INTEGER (FOREIGN KEY) | NULL        |
| discount_amount | DECIMAL               | DEFAULT     |
| final_amount    | DECIMAL               | DEFAULT     |
| status          | STRING                | DEFAULT     |
| payment_method  | STRING                | DEFAULT     |
| created_at      | DATETIME              | DEFAULT     |

---

### Slide 15: TABLE - ORDERITEM

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| order_id   | INTEGER (FOREIGN KEY) | NOT NULL    |
| product_id | INTEGER (FOREIGN KEY) | NOT NULL    |
| size       | STRING                | NOT NULL    |
| color      | STRING                | NULL        |
| quantity   | INTEGER               | NOT NULL    |
| price      | DECIMAL               | NOT NULL    |

---

### Slide 16: TABLE - REVIEW

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| product_id | INTEGER (FOREIGN KEY) | NOT NULL    |
| user_id    | INTEGER (FOREIGN KEY) | NOT NULL    |
| rating     | INTEGER               | NOT NULL    |
| comment    | TEXT                  | NOT NULL    |
| created_at | DATETIME              | DEFAULT     |

---

### Slide 17: TABLE - WISHLIST

| FIELD NAME | DATA TYPE             | DESCRIPTION |
| ---------- | --------------------- | ----------- |
| id         | INTEGER (PRIMARY KEY) | PRIMARY KEY |
| user_id    | INTEGER (FOREIGN KEY) | NOT NULL    |
| product_id | INTEGER (FOREIGN KEY) | NOT NULL    |
| created_at | DATETIME              | DEFAULT     |
