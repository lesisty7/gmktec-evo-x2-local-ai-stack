# Rocket.Chat Stack Example

This directory contains a public-safe environment example for a Rocket.Chat deployment backed by MongoDB.

## What It Shows

- external URL and port shaping
- a Docker Compose example for the stack
- MongoDB replica set related variables
- upload storage location
- SMTP wiring shape for notifications

## Included Files

- `.env.example`
- `docker-compose.example.yml`

## How to Use It

- copy `.env.example` to `.env`
- replace `ROOT_URL`, `MAIL_URL`, and any placeholder credentials
- adjust storage paths and ports to your own system
- review image versions before using the stack in production

## Notes

- the example does not attempt to document every Rocket.Chat option
- it focuses on the variables that shape the deployment boundary and supporting services
