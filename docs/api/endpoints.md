# ParkUPB API – Endpoints

## Autentificare

### POST /register  (Task 5)
- Creează un utilizator nou.
- Vezi docstring în app/routes/auth.py::register

### POST /login  (Task 5)
- Autentificare utilizator.
- Vezi docstring în app/routes/auth.py::login

---

## Parcări & locuri

### GET /parking/lots  (Task 6, 7, 8)
- Listează parcările (parking lots).

### GET /parking/spots  (Task 6, 7, 8)
- Listează locurile de parcare (parking spots), opțional filtrate.

---

## Rezervări

### POST /reservations/  (Task 9)
- Creează o rezervare nouă.

### DELETE /reservations/{id}  (Task 9)
- Anulează o rezervare.

### GET /reservations/my  (Task 10)
- Istoricul rezervărilor user-ului curent.

---

## Admin

### POST /admin/polygons  (Task 6)
- Salvează poligoanele desenate (GeoJSON).

### GET /admin/stats  (Task 11)
- Returnează statistici globale.
