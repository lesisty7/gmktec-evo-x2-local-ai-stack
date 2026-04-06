# Mattermost Stack Example

This directory contains a public-safe environment example for a Mattermost deployment with PostgreSQL and bootstrap automation.

## What It Shows

- database credentials and site URL shape
- bootstrap administrator variables
- persistent path layout for database, app data, and backups
- optional bootstrap toggles that are useful during first-time setup

## How to Use It

- copy `.env.example` to `.env`
- replace all placeholder credentials and email addresses
- set the public site URL to your own domain
- review bootstrap toggles before keeping them enabled in a live environment

## Notes

- first-boot bootstrap variables are operationally useful but should be treated carefully
- this example is intentionally smaller and safer than a direct export from a live stack
