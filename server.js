// server.js
const express = require('express');
const app = express();
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const multer = require('multer');

// SERVIR ARCHIVOS ESTÁTICOS:
// Los archivos de tu sitio (HTML, CSS, JS) se ubicarán en la carpeta "public".
app.use(express.static(path.join(__dirname, 'public')));

// Middlewares
app.use(cors());
app.use(express.json());

// Clave secreta para rutas de administración
const ADMIN_KEY = "tu_clave_secreta";

// Configuración de Multer para subir imágenes
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/");
  },
  filename: (req, file, cb) => {
    cb(null, "foto.jpg"); // Siempre se sobrescribe la misma foto
  }
});
const upload = multer({ storage });

// Servir la carpeta de imágenes "uploads"
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Conexión a SQLite y creación de la tabla si no existe
const db = new sqlite3.Database("./diario.db", (err) => {
  if (err) {
    console.error("Error al conectar con la base de datos:", err.message);
  } else {
    console.log("Base de datos conectada");
  }
});

db.run(
  `CREATE TABLE IF NOT EXISTS entradas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    contenido TEXT NOT NULL,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP
  )`
);

// Endpoints públicos
// Obtener las últimas 5 entradas
app.get('/entradas', (req, res) => {
  db.all("SELECT * FROM entradas ORDER BY fecha DESC LIMIT 5", [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// Obtener todas las entradas
app.get('/todas', (req, res) => {
  db.all("SELECT * FROM entradas ORDER BY fecha DESC", [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// Buscar entradas por palabra clave
app.get('/buscar', (req, res) => {
  const palabra = req.query.q;
  db.all(
    "SELECT * FROM entradas WHERE contenido LIKE ? ORDER BY fecha DESC",
    [`%${palabra}%`],
    (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(rows);
    }
  );
});

// Middleware para las rutas de administración
app.use('/admin', (req, res, next) => {
  if (req.headers["x-admin-key"] !== ADMIN_KEY) {
    return res.status(403).json({ error: "Acceso denegado" });
  }
  next();
});

// Rutas de administración
// Agregar una nueva entrada
app.post('/admin/nueva', (req, res) => {
  const { titulo, contenido } = req.body;
  if (!titulo || !contenido) {
    return res.status(400).json({ error: "Título y contenido son requeridos" });
  }
  db.run("INSERT INTO entradas (titulo, contenido) VALUES (?, ?)", [titulo, contenido], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ id: this.lastID, titulo, contenido });
  });
});

// Eliminar una entrada
app.delete('/admin/borrar/:id', (req, res) => {
  const id = req.params.id;
  db.run("DELETE FROM entradas WHERE id = ?", [id], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ mensaje: "Entrada eliminada" });
  });
});

// Modificar una entrada
app.put('/admin/modificar/:id', (req, res) => {
  const { titulo, contenido } = req.body;
  const id = req.params.id;
  if (!titulo || !contenido) {
    return res.status(400).json({ error: "Título y contenido son requeridos" });
  }
  db.run("UPDATE entradas SET titulo = ?, contenido = ? WHERE id = ?", [titulo, contenido, id], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ mensaje: "Entrada modificada" });
  });
});

// Subir foto (administración)
app.post('/admin/subir-foto', upload.single("foto"), (req, res) => {
  res.json({ mensaje: "Foto subida con éxito", url: "/uploads/foto.jpg" });
});

// Iniciar el servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
