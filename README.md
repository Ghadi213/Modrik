<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/modrik_banner_dark.jpg">
    <img src="assets/modrik_banner_light.jpg" alt="Modrik – Bioinformatics Platform for Genetic Variant Interpretation" width="640">
  </picture>
</p>

<h3 align="center">Bioinformatics Platform for Genetic Variant Interpretation</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Flutter-02569B?logo=flutter&logoColor=white" alt="Flutter">
  <img src="https://img.shields.io/badge/Dart-0175C2?logo=dart&logoColor=white" alt="Dart">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/OpenCRAVAT-Bioinformatics-2E7D32" alt="OpenCRAVAT">
  <img src="https://img.shields.io/badge/Firebase-Authentication-FFCA28?logo=firebase&logoColor=black" alt="Firebase">
  <img src="https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite">
</p>

Modrik is a cross-platform mobile application that integrates established bioinformatics resources to interpret genetic variants from Variant Call Format (VCF) files, with optional AI-assisted explanations and expert consultation.

## Overview

Modrik was developed to simplify genetic variant interpretation through one integrated bioinformatics workflow.

The platform supports both **individual** and **couple** genetic analyses by combining several bioinformatics resources into a single system. Users can upload VCF files, get annotated genetic findings, explore disease associations, request expert consultation, and receive optional AI-assisted explanations.

> The AI assistant is **not** part of the genetic analysis process. Unlike the bioinformatics pipeline, it is only there to help users understand their genetic findings and answer genetics-related questions.

To protect user privacy, genetic reports are stored **locally on the user's device** using SQLite, while authentication and operational services are managed securely through Firebase Authentication and backend APIs.

## Key Features

- Individual VCF Analysis
- Couple Genetic Analysis
- OpenCRAVAT Variant Annotation
- PanelApp Disease Interpretation
- Optional AI Genetic Assistant
- General Genetics Chat
- Expert Consultation
- Administrative Dashboard
- Arabic Disease Name Translation
- Firebase Authentication
- Local Report Storage (SQLite)

## System Architecture

The diagram below shows the overall architecture of Modrik: the mobile application, backend services, integrated bioinformatics resources, databases, and optional AI services.

<p align="center">
  <img src="assets/system_architecture.png" alt="Modrik system architecture" width="100%">
</p>

## Screenshots

<p align="center">
  <img src="assets/banner_1.png" alt="Modrik app screens" width="100%">
</p>

<p align="center">
  <img src="assets/banner_2.png" alt="Modrik app screens" width="100%">
</p>

## Technology Stack

| Layer | Technologies |
|---|---|
| Mobile Application | Flutter, Dart |
| Backend | Python, FastAPI |
| Bioinformatics | OpenCRAVAT, PanelApp |
| Authentication | Firebase Authentication |
| Databases | MySQL, SQLite |
| AI Services | Google Gemini API, OpenRouter API |
| Server | Linux, Nginx |

## Project Structure

```
Modrik/
├─ frontend/Modrik/          Flutter mobile application
│  └─ lib/
│     ├─ screens/            users, expert, admin and shared screens
│     ├─ services/           Calls to the backend API
│     ├─ widgets/            Reusable UI parts
│     ├─ models/             Report data models
│     ├─ l10n/               Arabic and English text
│     └─ theme/              Colours and text styles
├─ backend/                  Python FastAPI backend
│  ├─ main.py                API endpoints
│  ├─ database.py            MySQL connection
│  ├─ services/              Backend services
│  ├─ utils/                 Helper functions
│  ├─ requirements.txt
│  └─ .env.example           Settings template (copy to .env)
├─ assets/                   README images
└─ README.md
```

## Acknowledgments

This project integrates several open-source tools, public genomic resources, and cloud services:

- **OpenCRAVAT** – genetic variant annotation
- **PanelApp** – gene–disease relationship data
- **Google Gemini API** – optional AI assistant for explaining genetic findings
- **OpenRouter API** – Arabic translation of disease names
- **Firebase Authentication** – user authentication and access management
- **Flutter** – cross-platform mobile development framework
- **FastAPI** – backend API framework

## Team

Developed as a Computer Science Graduation Project by the Modrik Team.

[Ghadi Alrashdi](https://github.com/Ghadi213) · Hagar Naga · [Rudaynah Alghubishy](https://github.com/itsrudaynah) · Majd Alharbi

## Copyright

© 2026 Modrik Team.

This repository is provided for academic and portfolio purposes only. The source code is not licensed for redistribution or commercial use without prior permission from the project authors.
