if (document.getElementById('my-work-link')) {
  document.getElementById('my-work-link').addEventListener('click', () => {
    document.getElementById('my-work-section').scrollIntoView({behavior: "smooth"})
  })
}

function titleFromSlug(slug) {
  return slug
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function stripMarkdown(md) {
  return md
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!\[[^\]]*\]\([^\)]*\)/g, ' ')
    .replace(/\[[^\]]*\]\([^\)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[>*_~#-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function parseSimpleFrontMatter(markdown) {
  const trimmed = markdown.trimStart();
  if (!trimmed.startsWith('---')) {
    return { metadata: {}, body: markdown };
  }

  const endIndex = trimmed.indexOf('\n---', 3);
  if (endIndex === -1) {
    return { metadata: {}, body: markdown };
  }

  const rawMeta = trimmed.slice(3, endIndex).trim();
  const body = trimmed.slice(endIndex + 4).trimStart();
  const metadata = {};

  rawMeta.split('\n').forEach((line) => {
    const idx = line.indexOf(':');
    if (idx === -1) return;
    const key = line.slice(0, idx).trim().toLowerCase();
    const value = line.slice(idx + 1).trim().replace(/^['\"]|['\"]$/g, '');
    if (key) metadata[key] = value;
  });

  return { metadata, body };
}

function parsePostFromMarkdown(filename, markdown) {
  const slug = filename.replace(/\.md$/i, '');
  const { metadata, body } = parseSimpleFrontMatter(markdown);
  const headingMatch = body.match(/^#\s+(.+)$/m);
  const title = metadata.title || (headingMatch ? headingMatch[1].trim() : titleFromSlug(slug));
  const date = metadata.date || '';

  let description = metadata.description || '';
  if (!description) {
    const plain = stripMarkdown(body);
    description = plain.slice(0, 170) + (plain.length > 170 ? '...' : '');
  }

  return {
    slug,
    title,
    date,
    description,
    url: `./blog-pages/blog-template.html?post=${encodeURIComponent(slug)}`
  };
}

function normalizePostForCard(post) {
  const safePost = post || {};
  const slug = String(safePost.slug || '').trim();

  return {
    slug,
    title: safePost.title || (slug ? titleFromSlug(slug) : 'Untitled Post'),
    date: safePost.date || '',
    description: safePost.description || 'No description available.',
    url: `./blog-pages/blog-template.html?post=${encodeURIComponent(slug)}`
  };
}

async function discoverMarkdownFilesFromDirectory() {
  const res = await fetch('./markdown/', { cache: 'no-store' });
  if (!res.ok) return [];
  const html = await res.text();

  if (!/<html/i.test(html)) {
    return [];
  }

  const doc = new DOMParser().parseFromString(html, 'text/html');
  const names = new Set();

  doc.querySelectorAll('a[href]').forEach((a) => {
    const href = a.getAttribute('href') || '';
    let decoded = '';

    try {
      decoded = decodeURIComponent(href.split('/').pop() || '');
    } catch (error) {
      return;
    }

    if (/\.md$/i.test(decoded)) {
      names.add(decoded);
    }
  });

  return Array.from(names);
}

function getGitHubRepoInfo() {
  const host = window.location.hostname;
  if (!host.endsWith('github.io')) {
    return null;
  }

  const owner = host.split('.')[0];
  const segments = window.location.pathname.split('/').filter(Boolean);
  let repo = '';

  if (segments.length > 0 && !segments[0].endsWith('.html')) {
    repo = segments[0];
  }

  return { owner, repo };
}

async function discoverMarkdownFilesFromGitHubApi() {
  const info = getGitHubRepoInfo();
  if (!info) return [];

  const repoPath = info.repo ? `${info.repo}/` : '';
  const apiUrl = `https://api.github.com/repos/${info.owner}/${info.repo || `${info.owner}.github.io`}/contents/markdown`;
  const res = await fetch(apiUrl, { cache: 'no-store' });
  if (!res.ok) return [];

  const data = await res.json();
  if (!Array.isArray(data)) return [];

  return data
    .filter((item) => item && item.type === 'file' && /\.md$/i.test(item.name || ''))
    .map((item) => item.name);
}

async function discoverMarkdownFiles() {
  const fromDirectory = await discoverMarkdownFilesFromDirectory();
  if (fromDirectory.length > 0) return fromDirectory;

  const fromApi = await discoverMarkdownFilesFromGitHubApi();
  if (fromApi.length > 0) return fromApi;

  return [];
}

function postDateValue(dateText) {
  const value = Date.parse(dateText || '');
  return Number.isNaN(value) ? 0 : value;
}

function getFallbackPosts() {
  if (!Array.isArray(window.BLOG_POSTS) || window.BLOG_POSTS.length === 0) {
    return [];
  }

  const fallbackPosts = window.BLOG_POSTS
    .map((post) => normalizePostForCard(post))
    .filter((post) => post.slug);

  fallbackPosts.sort((a, b) => postDateValue(b.date) - postDateValue(a.date));
  return fallbackPosts;
}

function createBlogCard(post) {
  const url = post.url || '#';
  const displayDate = post.date || 'Undated';

  return `
    <div class="project-card"
         style="justify-content: space-between; transform-style: preserve-3d; transform: perspective(1000px); transition: transform 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94); cursor: pointer;"
         onmousemove="const rect = this.getBoundingClientRect(); const x = event.clientX - rect.left; const y = event.clientY - rect.top; const xPct = (x / rect.width - 0.5) * 2; const yPct = (y / rect.height - 0.5) * 2; this.style.transform = \`perspective(1000px) rotateX(\${-yPct * 10}deg) rotateY(\${xPct * 10}deg) scale3d(1.02, 1.02, 1.02)\`; this.style.boxShadow = \`\${-xPct * 10}px \${yPct * 10 + 10}px 20px rgba(0,0,0,0.1)\`; this.style.transition = 'none';"
         onmouseleave="this.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)'; this.style.boxShadow = 'none'; this.style.transition = 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94), box-shadow 0.5s';"
         onclick="window.location.href='${url}'">
      <div class="project-card-text-container" style="transform: translateZ(30px);">
        <div class="subheader-text project-title">${post.title}</div>
        <div class="body-text" style="font-size: 14px; opacity: 0.7; margin-bottom: -8px;">${displayDate}</div>
        <div class="body-text project-card-text">${post.description}</div>
      </div>
      <a class="button" href="${url}" style="transform: translateZ(40px);" onclick="event.stopPropagation();">
        <span class="button-text">Read Article</span>
        <img src="./assets/icons/arrow-right.svg" class="right-arrow-icon" alt="Right Arrow"/>
      </a>
    </div>
  `;
}

function renderNoPostsState(container, message) {
  if (!container) return;
  container.innerHTML = `<div class="body-text" style="opacity:0.7; margin-top: 8px;">${message}</div>`;
}

async function loadBlogPostsFromMarkdown() {
  const markdownFiles = await discoverMarkdownFiles();
  if (markdownFiles.length === 0) {
    return getFallbackPosts();
  }

  const posts = [];
  await Promise.all(markdownFiles.map(async (filename) => {
    try {
      const res = await fetch(`./markdown/${encodeURIComponent(filename)}?v=${Date.now()}`, { cache: 'no-store' });
      if (!res.ok) return;
      const markdown = await res.text();
      posts.push(parsePostFromMarkdown(filename, markdown));
    } catch (error) {
      console.warn('Failed to load markdown post:', filename, error);
    }
  }));

  if (posts.length === 0) {
    return getFallbackPosts();
  }

  posts.sort((a, b) => postDateValue(b.date) - postDateValue(a.date));
  return posts;
}

async function renderBlogSections() {
  const blogPostsContainer = document.getElementById('blog-posts-container');
  const latestPostsContainer = document.getElementById('latest-posts-container');

  if (!blogPostsContainer && !latestPostsContainer) {
    return;
  }

  if (blogPostsContainer) {
    renderNoPostsState(blogPostsContainer, 'Loading blog posts...');
  }
  if (latestPostsContainer) {
    renderNoPostsState(latestPostsContainer, 'Loading latest posts...');
  }

  const posts = await loadBlogPostsFromMarkdown();

  if (blogPostsContainer) {
    if (posts.length === 0) {
      renderNoPostsState(blogPostsContainer, 'No blog posts found yet. Add a markdown file in the markdown folder to publish one.');
    } else {
      blogPostsContainer.innerHTML = posts.map((post) => createBlogCard(post)).join('');
    }
  }

  if (latestPostsContainer) {
    if (posts.length === 0) {
      renderNoPostsState(latestPostsContainer, 'No latest posts yet.');
    } else {
      latestPostsContainer.innerHTML = posts.slice(0, 3).map((post) => createBlogCard(post)).join('');
    }
  }
}

renderBlogSections();


// --- Scroll Reveal Animation Logic ---
function revealOnScroll() {
  const reveals = document.querySelectorAll(".reveal");
  for (let i = 0; i < reveals.length; i++) {
    const windowHeight = window.innerHeight;
    const elementTop = reveals[i].getBoundingClientRect().top;
    const elementVisible = 100; // when to trigger the animation

    if (elementTop < windowHeight - elementVisible) {
      reveals[i].classList.add("active");
    }
  }
}

// Check once on load, then on scroll
window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);
// Also try immediately in case DOM is already loaded
revealOnScroll();

// --- Inject Project Feedback Form ---
// Automatically injects a minimal feedback form into any project page
function injectFeedbackForm() {
  // Check if we are on a project page (has #project-details or similar)
  const isProjectPage = document.getElementById("project-details") || window.location.pathname.includes("project-pages/");
  const mainContent = document.getElementById("main-content");
  const repoInfo = getGitHubRepoInfo();
  const siteBasePath = repoInfo && repoInfo.repo ? `/${repoInfo.repo}` : "";
  const sendIconSrc = `${siteBasePath}/assets/icons/arrow-right.svg`;
  
  // Prevent double-injection if called multiple times
  if (isProjectPage && mainContent && !document.getElementById("project-feedback")) {
    const feedbackHTML = `
      <div id="project-feedback" style="margin-top: 64px; padding: 40px; background: #fff; border-radius: 16px; border: 1px solid rgba(0,0,0,0.08); box-shadow: 0 10px 40px rgba(0,0,0,0.02);">
        <div class="subheader-text" style="margin-bottom: 8px;">Leave a Comment</div>
        <div class="body-text" style="font-size: 14px; opacity: 0.7; margin-bottom: 24px;">Share your thoughts anonymously or leave your name. Messages are sent securely.</div>
        
        <!-- Replace YOUR_FORMSPREE_ID with your actual Formspree ID (e.g., https://formspree.io/f/xyzqwpas) -->
        <form action="https://formspree.io/f/xkopqypa" method="POST" style="display: flex; flex-direction: column; gap: 16px;">
          
          <!-- Hidden field to know WHICH project they are commenting on -->
          <input type="hidden" name="project_page" value="${document.title}">
          
          <!-- Automatically redirect them back to this exact same page after they submit the message! -->
          <input type="hidden" name="_next" value="${window.location.href}">

          <div style="display: flex; flex-direction: column; gap: 8px;">
            <label style="font-family: inherit; font-weight: 600; font-size: 14px; color: #333;">Name (Optional)</label>
            <input type="text" name="name" placeholder="Anonymous" style="padding: 14px; border: 1px solid #eaeaea; border-radius: 8px; font-family: inherit; font-size: 15px; outline: none; background: #fafafa; transition: border-color 0.2s;">
          </div>

          <div style="display: flex; flex-direction: column; gap: 8px;">
            <label style="font-family: inherit; font-weight: 600; font-size: 14px; color: #333;">Message</label>
            <textarea name="message" required placeholder="What do you think about this project?" rows="4" style="padding: 14px; border: 1px solid #eaeaea; border-radius: 8px; font-family: inherit; font-size: 15px; resize: vertical; outline: none; background: #fafafa; transition: border-color 0.2s;"></textarea>
          </div>

          <button type="submit" class="button" style="margin-top: 8px; cursor: pointer; background: #111; color: white; border: none; align-self: flex-start; padding: 12px 24px; border-radius: 8px; transition: transform 0.2s ease, box-shadow 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 15px rgba(0,0,0,0.1)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
            <span class="button-text" style="color: white;">Send Message</span>
            <img src="${sendIconSrc}" class="right-arrow-icon" style="filter: invert(1); margin-left: 8px;" alt="Send"/>
          </button>
        </form>

        <style>
          #project-feedback input:focus, #project-feedback textarea:focus {
            border-color: #000 !important;
            background: #fff !important;
          }
        </style>
      </div>
    `;

    // Append to the bottom of the main content area
    mainContent.insertAdjacentHTML("beforeend", feedbackHTML);
    // Initialize reveal animations for the newly added content
    revealOnScroll();
  }
}

// Call it immediately
injectFeedbackForm();
// Also run on DOMContentLoaded just in case it loads too early
window.addEventListener("DOMContentLoaded", injectFeedbackForm);

