/* =====================================================================
   COMandFIN — SITE & LMS CONFIGURATION
   ---------------------------------------------------------------------
   This is the ONLY file you need to edit to connect the website to your
   LMS (Graphy, Teachable, Thinkific, LearnWorlds, TagMango, Moodle, etc.)
   and to update contact details. Every "Enroll", "Student Login" and
   "Free Demo" button on the site reads its link from here.

   Leave a value as "" (empty) and the site falls back to the enquiry form.
   See DEPLOYMENT.md for step-by-step instructions.
   ===================================================================== */
window.SITE_CONFIG = {
  brand: "COMandFIN",

  contact: {
    email: "info@comandfin.com",        // TODO: confirm official email
    phone: "",                          // e.g. "+91 98XXXXXXXX"
    whatsapp: "",                       // digits only with country code, e.g. "9198XXXXXXXX"
    address: "India",                   // TODO: registered office address
  },

  social: {
    linkedin: "",
    youtube: "",
    instagram: "",
  },

  /* ---------------- LMS CONNECTION ----------------
     name        : shown on buttons, e.g. "Graphy", "Teachable"
     loginUrl    : student login page of your LMS / school
     signupUrl   : optional new-student sign-up page
     courseUrls  : checkout / course landing page for each course on the LMS
                   (the key must match data-course="..." used on the site)
     openInNewTab: true opens the LMS in a new browser tab
  */
  lms: {
    name: "Student Portal",
    loginUrl: "",       // e.g. "https://learn.comandfin.com/login"
    signupUrl: "",      // e.g. "https://learn.comandfin.com/signup"
    openInNewTab: true,
    courseUrls: {
      "us-cma": "",               // e.g. "https://learn.comandfin.com/courses/us-cma"
      "us-cpa": "",
      "financial-modelling": "",
      "claude-training": "",
    },
  },

  /* ---------------- ENQUIRY FORM ----------------
     Static hosting cannot send email by itself. Paste a form endpoint from
     Formspree (https://formspree.io), Getform, or Web3Forms here.
     If left empty, the form opens the visitor's email app instead. */
  formEndpoint: "",
};
