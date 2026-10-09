# COMandFIN Website — Setup Guide

A fast, static website (plain HTML/CSS/JS). It has no database or server code, so it runs on
**any** host — GitHub Pages (free) or GoDaddy hosting — and connects to your GoDaddy domain.

```
index.html                  Home page
courses/                    US CMA, US CPA, Financial Modelling, Claude Training pages
login.html                  Student login (sends learners to your LMS)
labs/                       Financial Statement Analysis Learning Lab (free resource)
assets/js/site-config.js    <-- THE ONLY FILE YOU NEED TO EDIT (LMS links, contact details)
assets/img/                 Logos (logo.svg, logo-light.svg, claude-logo.svg, favicon.svg)
```

---

## 1. Connect your LMS (videos and study material)

Pick an LMS that hosts videos securely, takes payments in INR and gives students a login.
Good options for Indian finance educators:

| LMS | Best for | Custom domain (e.g. learn.comandfin.com) |
|---|---|---|
| **Graphy** | Indian creators, UPI/Razorpay, mobile app | Yes |
| **Teachable / Thinkific** | Global audience, mature course builder | Yes (paid plans) |
| **LearnWorlds** | Interactive video, assessments, white-label app | Yes |
| **TagMango / Exly** | Cohort and live-class focus, Indian payments | Yes |
| **Moodle (hosted)** | Universities and corporate programs, SCORM | Yes |

**Steps**
1. Create the 4 courses in your LMS. Upload the videos, PDFs and Excel files there.
2. Copy each course's checkout or landing URL, plus your student login URL.
3. Open `assets/js/site-config.js` and paste them in:
   ```js
   lms: {
     name: "Student Portal",
     loginUrl:  "https://learn.comandfin.com/login",
     signupUrl: "https://learn.comandfin.com/signup",
     courseUrls: {
       "us-cma": "https://learn.comandfin.com/courses/us-cma",
       "us-cpa": "https://learn.comandfin.com/courses/us-cpa",
       "financial-modelling": "https://learn.comandfin.com/courses/financial-modelling",
       "claude-training": "https://learn.comandfin.com/courses/claude-training",
     },
   },
   ```
4. Every **Enroll Now**, **Login** and **Student Portal** button on the site updates automatically.
   Until you fill in a URL, its button opens the enquiry form, so no link is ever broken.

**Recommended:** in your LMS, map a subdomain such as `learn.comandfin.com`. The LMS gives you
a CNAME value to add in GoDaddy DNS (step 3 below). Students then see one brand throughout.

---

## 2. Enquiry form

Static hosting cannot send email by itself. Create a free form at **Formspree** (formspree.io),
**Web3Forms** or **Getform**, then paste its endpoint into `formEndpoint` in `site-config.js`.
Leads then arrive in your inbox. If you leave it blank, the form opens the visitor's email app.

In the same file, also fill in `contact.email`, `contact.phone`, `contact.whatsapp` (this turns on
the WhatsApp button) and the `social` links.

---

## 3. Put the website live on your GoDaddy domain

### Option A — GitHub Pages + GoDaddy DNS (free hosting, recommended)
1. Merge this branch into `main`.
2. In the GitHub repo, go to **Settings → Pages**. Set Source to *Deploy from a branch*,
   choose `main` / root, and save.
3. Under **Custom domain**, enter `www.comandfin.com` and save. GitHub creates a `CNAME` file.
4. In GoDaddy, go to **My Products → Domain → DNS → Manage DNS** and set these records:

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | `<your-github-username>.github.io` |
   | CNAME | learn | *(value given by your LMS)* |

   First delete any existing GoDaddy "Parked" A record for `@`.
5. DNS changes take 15 minutes to 24 hours. After that, tick **Enforce HTTPS** in GitHub Pages.

### Option B — GoDaddy Web Hosting (cPanel)
1. In GoDaddy, open **Web Hosting → cPanel Admin → File Manager → public_html**.
2. Upload all files and folders from this repository, keeping the folder structure.
3. In cPanel, turn on the free **SSL** certificate. The domain already points to this hosting.

> GoDaddy's Website Builder cannot import custom HTML, so use Option A or B instead.

---

## 4. Checklist before going live
- [ ] Fill in `site-config.js`: LMS URLs, email, phone, WhatsApp, social links, form endpoint
- [ ] Confirm the course durations and replace the "AB" mentor placeholder with a photo
- [ ] Replace `assets/img/claude-logo.svg` with the official Claude logo from Anthropic's
      brand resources (keep the same filename) and follow Anthropic's brand guidelines
- [ ] If your domain is not `comandfin.com`, update it in `robots.txt`, `sitemap.xml` and the
      `canonical` tags (search and replace `www.comandfin.com`)
- [ ] Submit `sitemap.xml` in Google Search Console
