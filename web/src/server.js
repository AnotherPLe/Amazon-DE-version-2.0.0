const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const path = require('path');

const app = express();
const port = 3001;

// Cấu hình kết nối database
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root', // Thay đổi theo thông tin đăng nhập của bạn
  password: 'phuocle11001203', // Thay đổi theo mật khẩu của bạn
  database: 'olap_datn'
});

// Kết nối database
db.connect((err) => {
  if (err) {
    console.error('Lỗi kết nối database:', err);
    return;
  }
  console.log('Đã kết nối thành công với database');
});

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// API tìm kiếm sản phẩm
app.get('/api/search', (req, res) => {
  const keyword = req.query.keyword || '';
  const categoryID = req.query.categoryID;
  const priceGroup = req.query.priceGroup;

  let query = `
    SELECT 
      p.ASIN, 
      p.Product_Name, 
      p.Image_URL, 
      p.Color, 
      p.Overall_Rating, 
      p.Review_Count, 
      p.Weight, 
      p.Volumn, 
      p.ProductSizeTier, 
      p.Description,
      fce.price AS customer_price,
      fce.MainRankingValue,
      fce.Delivery_time_days,
      fce.AmazonGlobal_Shipping,
      fce.Estimated_Import_Charge,
      fce.PriceGroup
    FROM dim_product p
    LEFT JOIN (
        SELECT f1.ASIN, f1.price, f1.MainRankingValue, f1.Delivery_time_days, 
               f1.AmazonGlobal_Shipping, f1.Estimated_Import_Charge, f1.PriceGroup, f1.CategoryID
        FROM fact_customer_experience f1
        INNER JOIN (
            SELECT ASIN, MAX(dateID) AS max_date
            FROM fact_customer_experience
            GROUP BY ASIN
        ) f2 ON f1.ASIN = f2.ASIN AND f1.dateID = f2.max_date
    ) fce ON p.ASIN = fce.ASIN
    LEFT JOIN dim_product_category dpc ON p.ASIN = dpc.ASIN
    WHERE 1=1
  `;
  const params = [];
  if (keyword) {
    query += ' AND (p.product_name LIKE ? OR p.description LIKE ?)';
    params.push(`%${keyword}%`, `%${keyword}%`);
  }
  if (categoryID) {
    query += ' AND dpc.CategoryID = ?';
    params.push(categoryID);
  }
  if (priceGroup) {
    query += ' AND fce.PriceGroup = ?';
    params.push(priceGroup);
  }
  query += ' LIMIT 50';

  db.query(query, params, (err, results) => {
    if (err) {
      console.error('Lỗi truy vấn:', err);
      res.status(500).json({ error: 'Lỗi truy vấn database' });
      return;
    }
    res.json(results);
  });
});

// API lấy danh sách danh mục
app.get('/api/categories', (req, res) => {
  db.query('SELECT CategoryID, Category FROM dim_category ORDER BY Category', (err, results) => {
    if (err) {
      res.status(500).json({ error: 'Lỗi truy vấn danh mục' });
      return;
    }
    res.json(results);
  });
});

// API lấy danh sách nhóm giá
app.get('/api/price-groups', (req, res) => {
  db.query('SELECT DISTINCT PriceGroup FROM fact_customer_experience WHERE PriceGroup IS NOT NULL ORDER BY PriceGroup', (err, results) => {
    if (err) {
      res.status(500).json({ error: 'Lỗi truy vấn nhóm giá' });
      return;
    }
    res.json(results.map(r => r.PriceGroup));
  });
});

// API chi tiết sản phẩm
app.get('/api/product/:asin', (req, res) => {
  const asin = req.params.asin;
  const query = `
    SELECT 
      p.ASIN, 
      p.Product_Name, 
      p.Image_URL, 
      p.Color, 
      p.Overall_Rating, 
      p.Review_Count, 
      p.Weight, 
      p.Volumn, 
      p.ProductSizeTier, 
      p.Description,
      fce.price AS customer_price,
      fce.MainRankingValue,
      fce.Delivery_time_days,
      fce.AmazonGlobal_Shipping,
      fce.Estimated_Import_Charge,
      fce.PriceGroup
    FROM dim_product p
    LEFT JOIN (
        SELECT f1.ASIN, f1.price, f1.MainRankingValue, f1.Delivery_time_days, 
               f1.AmazonGlobal_Shipping, f1.Estimated_Import_Charge, f1.PriceGroup, f1.CategoryID
        FROM fact_customer_experience f1
        INNER JOIN (
            SELECT ASIN, MAX(dateID) AS max_date
            FROM fact_customer_experience
            GROUP BY ASIN
        ) f2 ON f1.ASIN = f2.ASIN AND f1.dateID = f2.max_date
    ) fce ON p.ASIN = fce.ASIN
    WHERE p.ASIN = ?
    LIMIT 1
  `;
  db.query(query, [asin], (err, results) => {
    if (err) {
      console.error('Lỗi truy vấn:', err);
      res.status(500).json({ error: 'Lỗi truy vấn database' });
      return;
    }
    if (results.length === 0) {
      res.status(404).json({ error: 'Không tìm thấy sản phẩm' });
      return;
    }
    res.json(results[0]);
  });
});

// API thống kê sản phẩm theo quốc gia (Automotive)
app.get('/api/stats/country', (req, res) => {
  const query = `
    SELECT g.CountryOfOrigin, COUNT(*) as count
    FROM fact_product_overview f
    JOIN dim_geolocation g ON f.locationID = g.locationID
    JOIN dim_category c ON f.CategoryID = c.CategoryID
    WHERE c.Category LIKE '%automotive%'
    GROUP BY g.CountryOfOrigin
    ORDER BY count DESC
    LIMIT 10
  `;
  db.query(query, (err, results) => {
    if (err) return res.status(500).json({ error: 'Lỗi truy vấn country' });
    res.json(results);
  });
});

// API thống kê sản phẩm theo danh mục (Automotive)
app.get('/api/stats/category', (req, res) => {
  const query = `
    SELECT c.Category, COUNT(*) as count
    FROM fact_product_overview f
    JOIN dim_category c ON f.CategoryID = c.CategoryID
    WHERE c.Category LIKE '%automotive%'
    GROUP BY c.Category
    ORDER BY count DESC
    LIMIT 10
  `;
  db.query(query, (err, results) => {
    if (err) return res.status(500).json({ error: 'Lỗi truy vấn category' });
    res.json(results);
  });
});

// API thống kê sản phẩm theo nhóm giá (Automotive)
app.get('/api/stats/price-group', (req, res) => {
  const query = `
    SELECT fce.PriceGroup, COUNT(*) as count
    FROM fact_customer_experience fce
    JOIN dim_category c ON fce.CategoryID = c.CategoryID
    WHERE c.Category LIKE '%automotive%'
    GROUP BY fce.PriceGroup
    ORDER BY count DESC
    LIMIT 10
  `;
  db.query(query, (err, results) => {
    if (err) return res.status(500).json({ error: 'Lỗi truy vấn price group' });
    res.json(results);
  });
});

app.listen(port, () => {
  console.log(`Server đang chạy tại http://localhost:${port}`);
}); 