
---

## **1. Connection & General**

| Command                                           | Description                    |
| ------------------------------------------------- | ------------------------------ |
| `\c [dbname] [user]` / `\connect [dbname] [user]` | Connect to a database.         |
| `\q`                                              | Quit `psql`.                   |
| `\! [command]`                                    | Execute a shell command.       |
| `\conninfo`                                       | Show current connection info.  |
| `\timing`                                         | Toggle query execution timing. |

---

## **2. Database & Schemas**

| Command        | Description         |
| -------------- | ------------------- |
| `\l` / `\list` | List all databases. |
| `\dn`          | List schemas.       |

---

## **3. Tables, Views & Sequences**

| Command       | Description                                  |
| ------------- | -------------------------------------------- |
| `\d`          | List tables, views, and sequences.           |
| `\dt`         | List tables only.                            |
| `\dv`         | List views only.                             |
| `\ds`         | List sequences only.                         |
| `\di`         | List indexes only.                           |
| `\dm`         | List materialized views.                     |
| `\dT`         | List data types.                             |
| `\dC`         | List conversions.                            |
| `\dFd`        | List foreign data wrappers.                  |
| `\dF`         | List foreign tables.                         |
| `\d [table]`  | Show table structure.                        |
| `\d+ [table]` | Show table with extra info (size, comments). |
| `\dp` / `\z`  | Show access privileges.                      |
| `\sv`         | List sequences.                              |
| `\dE`         | List event triggers.                         |

---

## **4. Functions & Roles**

| Command       | Description                     |
| ------------- | ------------------------------- |
| `\df`         | List functions.                 |
| `\df+`        | List functions with extra info. |
| `\du` / `\dg` | List roles/users.               |

---

## **5. Output & Formatting**

| Command                  | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| `\x`                     | Toggle expanded table output.                              |
| `\H`                     | Output results as HTML table.                              |
| `\a`                     | Toggle unaligned output (no formatting).                   |
| `\C [title]`             | Set title for query output.                                |
| `\t`                     | Toggle showing column headers and row count.               |
| `\pset [option] [value]` | Set output formatting options (border, pager, null, etc.). |

---

## **6. Scripts & Files**

| Command            | Description                                     |
| ------------------ | ----------------------------------------------- |
| `\i [file.sql]`    | Execute SQL script from file.                   |
| `\ir [file.sql]`   | Execute SQL script relative to current file.    |
| `\o [file]`        | Send query output to file.                      |
| `\g [file]`        | Execute query buffer; optionally write to file. |
| `\watch [seconds]` | Repeat last query every N seconds.              |

---

## **7. Variables**

| Command               | Description                                       |
| --------------------- | ------------------------------------------------- |
| `\set [name] [value]` | Set a `psql` variable.                            |
| `\unset [name]`       | Unset variable.                                   |
| `\echo [text]`        | Print text or variable value (`\echo :variable`). |

---


