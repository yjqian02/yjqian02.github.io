---
# Leave the homepage title empty to use the site title
title: ""
date: 2022-10-24
type: landing

design:
  spacing: "3rem"

sections:
  - block: markdown
    id: bio
    content:
      title: ""
      text: |-
        <div class="homepage-hero">
          <div class="hero-left">
            <img src="/media/alice-avatar.jpg" alt="Alice Qian" class="hero-avatar">
            <div class="hero-identity">
              <h1 class="hero-name">Alice Qian</h1>
              <p class="hero-role">Ph.D. Student · <a href="https://hcii.cmu.edu">CMU HCII</a></p>
            </div>
            <nav class="hero-links">
              <a href="mailto:aqzhang@andrew.cmu.edu">Email</a>
              <a href="https://scholar.google.com/citations?hl=en&user=9EeaJAkAAAAJ">Scholar</a>
              <a href="https://github.com/yjqian02">GitHub</a>
              <a href="https://www.linkedin.com/in/alice-qian-2775431b6/">LinkedIn</a>
              <a href="https://orcid.org/0009-0005-6407-6981">ORCID</a>
            </nav>
            <a href="/uploads/resume.pdf" class="hero-cv-btn">Download CV →</a>
            <div class="hero-news">
              <h3 class="bio-section-heading">Recent News</h3>
              <ul class="bio-news-list">
                <li><strong>May 2025.</strong> Paper accepted at CSCW 2025: "AURA: Supporting Responsible AI Content Work"</li>
                <li><strong>Apr 2025.</strong> Presented at CHI 2025 workshop on AI safety and red teaming</li>
                <li><strong>Sep 2024.</strong> Started Ph.D. at Carnegie Mellon University HCII</li>
                <li><strong>May 2024.</strong> Graduated with B.S. Computer Science from University of Minnesota</li>
              </ul>
            </div>
          </div>
          <div class="hero-right">
            <p>Hi! I am a Ph.D. student in the Human-Computer Interaction Institute (HCII) at Carnegie Mellon University advised by <a href="https://www.hcii.cmu.edu/people/hong-shen">Hong Shen</a> and <a href="https://www.lauradabbish.com/">Laura Dabbish</a>. I collaborated with <a href="https://www.jinasuh.com/">Jina Suh</a>, <a href="https://marylgray.org/">Mary L. Gray</a>, and <a href="https://ischool.uw.edu/people/faculty/profile/marycz">Mary Czerwinski</a> at Microsoft Research on research focused on identifying and addressing AI harms through red teaming.</p>
            <p>Prior to the start of my Ph.D., I was fortunate to have the opportunity to explore human-centered research across a few different institutions. At the University of Minnesota, I worked with <a href="https://steviechancellor.com/">Stevie Chancellor</a> on mental health content moderation. At the University of Washington, I collaborated with <a href="https://homes.cs.washington.edu/~axz/">Amy X. Zhang</a> to study personalized content moderation. And, at Rutgers University, I worked with <a href="https://shagunjhaver.com/">Shagun Jhaver</a> examining user perspectives on content moderation.</p>
            <p>Broadly, my research interests span the areas of AI safety, AI ethics, red teaming, content moderation, social computing, future of work, and responsible AI. I aim to <strong>build processes and tools to support the human infrastructure within AI development, enabling safer AI systems through practices such as AI red teaming.</strong> I am a recipient of the National Science Foundation (NSF) Graduate Research Fellowship Program (GRFP). My research has since been supported by the <a href="https://www.nist.gov/">National Institute of Standards and Technology (NIST)</a> and <a href="https://www.microsoft.com/en-us/research/academic-program/ai-society-fellows/fellows/">Microsoft</a>.</p>
            <p>Outside of my work, I'm passionate about mentorship, encouraging broader participation in computing, and supporting students interested in doing research. I'm always happy to chat about potential collaborations or research 😊.</p>
          </div>
        </div>
    design:
      spacing:
        padding: ["0", "0", "0", "0"]

  - block: markdown
    id: info
    content:
      title: ""
      text: |-
        <div class="bio-info-row">
          <div class="bio-col bio-col-education">
            <h3 class="bio-section-heading">Education</h3>
            <ul class="bio-education-list">
              <li>
                <span class="bio-edu-degree">Ph.D. Computer Science</span>
                <span class="bio-edu-institution">Carnegie Mellon University</span>
                <span class="bio-edu-years">2024 – present</span>
              </li>
              <li>
                <span class="bio-edu-degree">B.S. Computer Science</span>
                <span class="bio-edu-institution">University of Minnesota</span>
                <span class="bio-edu-years">2020 – 2024</span>
              </li>
            </ul>
          </div>
          <div class="bio-col bio-col-interests">
            <h3 class="bio-section-heading">Interests</h3>
            <ul class="bio-interests-list">
              <li>human infrastructure for AI 👩🏻</li>
              <li>AI evaluation ✅</li>
              <li>future of work 👩🏻‍💻</li>
              <li>social computing 🌐</li>
            </ul>
          </div>
        </div>
    design:
      spacing:
        padding: ["0", "0", "0", "0"]

  - block: collection
    id: pubs
    content:
      title: Publications
      text: ""
      filters:
        folders:
          - publication
        exclude_featured: false
    design:
      view: article-grid
---
