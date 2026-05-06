# IT Security Policy

**Version:** 2.4 | **Last reviewed:** January 2025 | **Owner:** IT Department

## Purpose

This policy establishes minimum security standards for all employees, contractors, and third parties who access Acme Corp's systems, data, or networks. Non-compliance may result in disciplinary action.

## Password Requirements

All company accounts must use passwords that meet the following criteria:
- Minimum 14 characters
- At least one uppercase letter, one lowercase letter, one number, and one special character
- Not reused from any of the previous 12 passwords
- Changed every 90 days for privileged accounts; annually for standard accounts

Passwords must never be shared with colleagues, written on physical media, or stored in unencrypted text files.

## Multi-Factor Authentication

MFA is mandatory for:
- All email accounts (Google Workspace)
- Company VPN
- Cloud service dashboards (AWS, GCP)
- Code repositories (GitHub)
- Finance systems

The approved MFA method is an authenticator app (Google Authenticator or Authy). SMS-based MFA is not permitted for privileged systems.

## Device Management

All company-issued devices are enrolled in our Mobile Device Management (MDM) platform. Employees must not disable MDM profiles. Personal devices may only access company data via approved applications and must have a screen lock enabled.

Devices must be reported lost or stolen to IT within two hours of discovery. IT reserves the right to remotely wipe any enrolled device.

## VPN Usage

The company VPN (Wireguard-based) must be active whenever accessing internal systems from outside the office. VPN credentials must not be shared. Split tunnelling is disabled; all traffic routes through the VPN gateway when connected.

## Data Classification

| Level | Description | Examples |
|-------|-------------|---------|
| Public | Approved for external sharing | Marketing materials, public website content |
| Internal | Default; no external sharing without approval | Policies, meeting notes, project plans |
| Confidential | Restricted; need-to-know basis | Customer PII, financial results, legal documents |
| Restricted | Highest sensitivity; explicit authorisation required | IP, acquisition plans, personal health data |

## Acceptable Use

Company systems are for business use. Incidental personal use is permitted but must not consume excessive bandwidth, involve unlicensed software, or access illegal content. Cryptocurrency mining on company infrastructure is strictly prohibited.

## Incident Reporting

Security incidents must be reported to security@acmecorp.com and the IT helpdesk immediately. An incident is defined as any suspected unauthorised access, data loss, phishing attempt, or malware infection. Do not attempt to investigate or remediate incidents without IT guidance.

## Software and Patching

Only software approved by the IT department may be installed on company devices. Operating system and application patches are applied automatically through MDM within 72 hours of release. Employees must not defer mandatory updates.
