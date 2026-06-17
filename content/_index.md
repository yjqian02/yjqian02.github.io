---
# Leave the homepage title empty to use the site title
title: ""
date: 2022-10-24
type: landing

design:
  spacing: "4rem"

sections:
  - block: resume-biography-3
    id: bio
    content:
      # Choose a user profile to display (a folder name within `content/authors/`)
      username: admin
      text: ""
      # Show a call-to-action button under your biography? (optional)
      button:
        text: Download CV
        url: uploads/resume.pdf
    design:
      css_class: system
      # background:
      #   color: white
        # image:
        #   # Add your image background to `assets/media/`.
        #   filename: 
        #   filters:
        #     brightness: 0.5
        #   size: cover
        #   position: center
        #   parallax: false
  # - block: markdown
  #   content:
  #     title: '📚 My Research'
  #     subtitle: ''
  #     text: |-
  #       I'm a Ph.D. Student at Carnegie Mellon University. My research investigates the human infrastructure underpinning the AI development pipeline, using a mixed-methods approach to examine how data work and workplace well-being intersect with AI development efforts.
        
  #       I'm always open to meeting folks with shared interests. Please email me if you want to chat 😃
  #   design:
  #     columns: '1'
  # - block: collection
  #   id: papers
  #   content:
  #     title: Featured Publications
  #     filters:
  #       folders:
  #         - publication
  #       featured_only: true
  #   design:
  #     view: article-grid
  #     columns: 2
  - block: markdown
    id: news
    content:
      title: ""
      text: |-
        <div class="bio-info-row">
          <div class="bio-col bio-col-news">
            <h3 class="bio-section-heading">Recent News</h3>
            <ul class="bio-news-list">
              <li><strong>May 2025</strong> — Paper accepted at CSCW 2025: "AURA: Supporting Responsible AI Content Work"</li>
              <li><strong>Apr 2025</strong> — Presented at CHI 2025 workshop on AI safety and red teaming</li>
              <li><strong>Sep 2024</strong> — Started Ph.D. at Carnegie Mellon University HCII</li>
              <li><strong>May 2024</strong> — Graduated with B.S. Computer Science from University of Minnesota</li>
            </ul>
          </div>
          <div class="bio-col bio-col-right">
            <div class="bio-right-section">
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
            <div class="bio-right-section">
              <h3 class="bio-section-heading">Interests</h3>
              <ul class="bio-interests-list">
                <li>human infrastructure for AI 👩🏻</li>
                <li>AI evaluation ✅</li>
                <li>future of work 👩🏻‍💻</li>
                <li>social computing 🌐</li>
              </ul>
            </div>
          </div>
        </div>
    design:
      spacing:
        padding: ["0", "0", "0", "0"]

  - block: collection
    id: pubs
    content:
      title: Recent Publications
      text: ""
      filters:
        folders:
          - publication
        exclude_featured: false
    design:
      view: article-grid
  # - block: collection
  #   id: talks
  #   content:
  #     title: Recent & Upcoming Talks
  #     filters:
  #       folders:
  #         - event
  #   design:
  #     view: article-grid
  #     columns: 1
  # - block: collection
  #   id: news
  #   content:
  #     title: Recent News
  #     subtitle: ''
  #     text: ''
  #     # Page type to display. E.g. post, talk, publication...
  #     page_type: post
  #     # Choose how many pages you would like to display (0 = all pages)
  #     count: 5
  #     # Filter on criteria
  #     filters:
  #       author: ""
  #       category: ""
  #       tag: ""
  #       exclude_featured: true
  #       exclude_future: false
  #       exclude_past: false
  #       publication_type: ""
  #     # Choose how many pages you would like to offset by
  #     offset: 0
  #     # Page order: descending (desc) or ascending (asc) date.
  #     order: desc
  #   design:
  #     # Choose a layout view
  #     view: date-title-summary
  #     # Reduce spacing
  #     spacing:
  #       padding: [0, 0, 0, 0]
#   - block: cta-card
#     demo: false # Only display this section in the Hugo Blox Builder demo site
#     content:
#       title: 👉 Build your own academic website like this
#       text: |-
#         This site is generated by Hugo Blox Builder - the FREE, Hugo-based open source website builder trusted by 250,000+ academics like you.

#         <a class="github-button" href="https://github.com/HugoBlox/hugo-blox-builder" data-color-scheme="no-preference: light; light: light; dark: dark;" data-icon="octicon-star" data-size="large" data-show-count="true" aria-label="Star HugoBlox/hugo-blox-builder on GitHub">Star</a>

#         Easily build anything with blocks - no-code required!
        
#         From landing pages, second brains, and courses to academic resumés, conferences, and tech blogs.
#       button:
#         text: Get Started
#         url: https://hugoblox.com/templates/
    # design:
    #   card:
    #     # Card background color (CSS class)
    #     css_class: "bg-primary-700"
    #     css_style: ""
---