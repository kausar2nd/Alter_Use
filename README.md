# AlterUSE – Recycling Rewards Web App

A simple Flask + MySQL app to submit recyclable items, earn points, view history, update profile, and withdraw points.

## Stack

- Backend: Python, Flask, mysql-connector-python
- Frontend: HTML, CSS, JavaScript
- DB: MySQL

## Project structure

```
AlterUSE/
├─ app.py
├─ templates/
│  ├─ index.html
│  ├─ signup.html
│  └─ dashboard.html
├─ static/
│  ├─ login_signup_style.css
│  ├─ dashboard_style.css
│  └─ dashboard_script.js
```

## Database schema

```
CREATE DATABASE IF NOT EXISTS alteruse;
USE alteruse;

CREATE TABLE IF NOT EXISTS user (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  user_name VARCHAR(100) NOT NULL,
  user_email VARCHAR(255) NOT NULL UNIQUE,
  user_password VARCHAR(255) NOT NULL,
  user_location VARCHAR(255) DEFAULT '',
  user_points INT NOT NULL DEFAULT 0,
  user_joining_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  bottles INT NOT NULL DEFAULT 0,
  cans INT NOT NULL DEFAULT 0,
  cups INT NOT NULL DEFAULT 0,
  user_history_branch VARCHAR(100) NOT NULL,
  user_history_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (user_id),
  CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES user(user_id)
    ON DELETE CASCADE
);
```
