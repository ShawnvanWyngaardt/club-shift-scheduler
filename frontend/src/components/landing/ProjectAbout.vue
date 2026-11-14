<script setup lang="ts">
import githubIcon from "@/assets/landing/icon-github.svg";
import linkedinIcon from "@/assets/landing/icon-linkedin.svg";

const GITHUB_URL = "https://github.com/ShawnvanWyngaardt/club-shift-scheduler";
const LINKEDIN_URL = "https://www.linkedin.com/in/shawn-van-wyngaardt/";
</script>

<template>
  <footer class="about" aria-labelledby="about-title">
    <h2 id="about-title" class="eyebrow">About this project</h2>

    <div class="about-grid">
      <div class="about-links">
        <a :href="GITHUB_URL" target="_blank">Read how it was built</a>
        <a href="/docs" target="_blank">API documentation</a>

        <div class="social">
          <a :href="GITHUB_URL" aria-label="The code on GitHub" target="_blank">
            <img
              :src="githubIcon"
              alt=""
              width="24"
              height="24"
              title="Club Shift Scheduler | Github"
            />
          </a>
          <a
            :href="LINKEDIN_URL"
            aria-label="Shawn van Wyngaardt on LinkedIn"
            target="_blank"
          >
            <img
              :src="linkedinIcon"
              alt=""
              width="24"
              height="24"
              Title="Shawn van Wyngaardt | LinkedIn"
            />
          </a>
        </div>
      </div>

      <div class="about-text">
        <p>
          Built by Shawn van Wyngaardt as a hands-on way to learn Python, with FastAPI,
          Vue 3 and PostgreSQL. The plans, decisions and a day-by-day build journal are in
          the repository.
        </p>
      </div>
    </div>
    <div class="about-text">
      <p class="legal">
        © 2026 Shawn van Wyngaardt. Source available on GitHub, all rights reserved.
      </p>
    </div>
  </footer>
</template>

<style scoped>
/* TODO: Refactor to use root colour variables */
.about {
  --about-link: #909cc2;
  --about-text: #f8f5fb;
  --about-eyebrow: #f0531c;
  --about-hover: #f58a07;

  margin-top: 96px;
}

.eyebrow {
  font-family: "Roboto Mono", ui-monospace, monospace;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em; /* 0.78px */
  text-transform: uppercase;
  color: var(--about-eyebrow);
  margin: 0;
}

.about-grid {
  display: flex;
  flex-direction: column;
  gap: 32px;
  margin-top: 18px;
}

.about-links {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}
.about-links > a {
  font-size: 14px;
  line-height: 24px;
  font-weight: 600;
  color: var(--about-link);
  text-decoration: none;
}
.about-links > a:hover {
  color: var(--about-hover);
  text-decoration: underline;
}

.social {
  display: flex;
  gap: 4px;
  margin-top: 24px;
  margin-left: -10px;
}
.social a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
}

a:focus-visible {
  outline: 3px solid var(--about-hover);
  outline-offset: 2px;
  border-radius: 6px;
}

.about-text p {
  font-size: 13px;
  line-height: 24px;
  color: var(--about-text);
  margin: 0;
  max-width: 416px;
}
.about-text .legal {
  font-size: 12px;
  font-weight: 500;
  color: var(--about-link);
  margin-top: 40px;
  max-width: none;
  text-align: center;
}

@media (min-width: 960px) {
  .about {
    margin-left: 23px; /* same left edge as the How it works heading */
  }
  .about-grid {
    display: grid;
    grid-template-columns: 254px 444px;
    gap: 0;
  }
  .about-text .legal {
    margin-top: 92px; /* the copyright line sits at the bottom of the panel */
  }
}
</style>
