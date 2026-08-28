#!/usr/bin/env ruby
# Lightweight Jekyll-compatible static builder for local preview
require 'fileutils'
require 'yaml'
require 'liquid'
require 'kramdown'
require 'date'

SITE_DIR = '_site'
FileUtils.mkdir_p(SITE_DIR)

# Copy static assets
['css', 'js', 'assets', 'project-pages'].each do |dir|
  dest = File.join(SITE_DIR, dir)
  FileUtils.rm_rf(dest) if Dir.exist?(dest)
  FileUtils.cp_r(dir, dest) if Dir.exist?(dir)
end

# Load books data
books = []
if File.exist?('_data/books.yml')
  books = YAML.safe_load(File.read('_data/books.yml'), permitted_classes: [Date]) || []
end

# Load and render posts
posts = []
if Dir.exist?('_posts')
  post_layout = File.read('_layouts/post.html')
  
  Dir.glob('_posts/*.md').sort.reverse.each do |post_file|
    content = File.read(post_file)
    meta = {}
    body = content
    
    if content.start_with?('---')
      parts = content.split('---', 3)
      if parts.size >= 3
        meta = YAML.safe_load(parts[1], permitted_classes: [Date]) || {}
        body = parts[2] || ''
      end
    end
    
    filename = File.basename(post_file, '.md')
    date_match = filename.match(/^(\d{4}-\d{2}-\d{2})-(.*)$/)
    if date_match
      date_str = date_match[1]
      slug = date_match[2]
    else
      date_str = meta['date'].to_s
      slug = filename
    end
    
    # 1. Determine Title & clean duplicate body heading
    if meta['title'] && !meta['title'].to_s.strip.empty?
      title = meta['title'].to_s.strip
      # If body starts with an H1 heading matching title, strip it to prevent duplicate title
      if body =~ /\A\s*#\s+(.*?)\n+/
        first_h1 = $1.strip
        if first_h1.downcase == title.downcase || first_h1.empty?
          body = body.sub(/\A\s*#\s+.*?\n+/, '')
        end
      end
    elsif body =~ /\A\s*#\s+(.+?)\s*$/
      title = $1.strip
      body = body.sub(/\A\s*#\s+.*?\n+/, '')
    else
      title = slug.gsub('-', ' ').capitalize
    end

    # 2. Determine Description
    if meta['description'] && !meta['description'].to_s.strip.empty?
      description = meta['description'].to_s.strip
    else
      # Extract first paragraph from body as description
      paragraphs = body.split(/\n\s*\n/).map(&:strip).reject { |p| p.empty? || p.start_with?('#') }
      first_p = paragraphs.first || ''
      clean_p = first_p.gsub(/[#*_`\[\]]/, '').strip
      description = clean_p.length > 140 ? clean_p[0..137] + '...' : clean_p
    end
    
    url = "/blog/#{slug}/"
    
    # Render post markdown body
    html_body = Kramdown::Document.new(body).to_html
    
    # Render layout
    post_context = {
      'page' => meta.merge({
        'title' => title,
        'date' => Date.parse(date_str.to_s),
        'url' => url,
        'slug' => slug
      }),
      'content' => html_body,
      'site' => { 'title' => "Phuc's Portfolio" }
    }
    
    rendered_post = Liquid::Template.parse(post_layout).render(post_context)
    
    # Write post output
    post_out_dir = File.join(SITE_DIR, 'blog', slug)
    FileUtils.mkdir_p(post_out_dir)
    File.write(File.join(post_out_dir, 'index.html'), rendered_post)
    
    posts << {
      'title' => title,
      'date' => Date.parse(date_str.to_s),
      'description' => description,
      'url' => url,
      'slug' => slug
    }
  end
end

site_context = {
  'site' => {
    'title' => "Phuc's Portfolio",
    'posts' => posts,
    'data' => { 'books' => books }
  }
}

# Helper to render liquid page
def render_page(file, context)
  raw = File.read(file)
  cleaned = raw.gsub(/\A---[\s\S]*?---\n/, '') # Strip front-matter
  template = Liquid::Template.parse(cleaned)
  template.render(context)
end

# Render core pages
['index.html', 'blog.html', 'books.html'].each do |page|
  if File.exist?(page)
    rendered = render_page(page, site_context)
    File.write(File.join(SITE_DIR, page), rendered)
  end
end

puts "[✓] Site built successfully into #{SITE_DIR}/ (#{posts.size} posts, #{books.size} books)"
