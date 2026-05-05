'use client';

import { useState, useCallback } from 'react';
import MarkdownRenderer from '@/components/MarkdownRenderer';

type Page = 'home' | 'storyboard' | 'projects' | 'settings';

// SVG Icons (inline, no emoji)
const Icons = {
  home: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
      <polyline points="9 22 9 12 15 12 15 22"></polyline>
    </svg>
  ),
  fileText: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="16" y1="13" x2="8" y2="13"></line>
      <line x1="16" y1="17" x2="8" y2="17"></line>
      <polyline points="10 9 9 9 8 9"></polyline>
    </svg>
  ),
  folder: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"></circle>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </svg>
  ),
  upload: (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
      <polyline points="17 8 12 3 7 8"></polyline>
      <line x1="12" y1="3" x2="12" y2="15"></line>
    </svg>
  ),
  download: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
      <polyline points="7 10 12 15 17 10"></polyline>
      <line x1="12" y1="15" x2="12" y2="3"></line>
    </svg>
  ),
  refresh: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10"></polyline>
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
    </svg>
  ),
  check: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  ),
  zap: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
    </svg>
  ),
  globe: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="2" y1="12" x2="22" y2="12"></line>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
    </svg>
  ),
  search: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"></circle>
      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>
  ),
  cpu: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
      <rect x="9" y="9" width="6" height="6"></rect>
      <line x1="9" y1="1" x2="9" y2="4"></line>
      <line x1="15" y1="1" x2="15" y2="4"></line>
      <line x1="9" y1="20" x2="9" y2="23"></line>
      <line x1="15" y1="20" x2="15" y2="23"></line>
      <line x1="20" y1="9" x2="23" y2="9"></line>
      <line x1="20" y1="14" x2="23" y2="14"></line>
      <line x1="1" y1="9" x2="4" y2="9"></line>
      <line x1="1" y1="14" x2="4" y2="14"></line>
    </svg>
  ),
  file: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
      <polyline points="13 2 13 9 20 9"></polyline>
    </svg>
  ),
};

const navItems: { id: Page; label: string; icon: React.ReactNode }[] = [
  { id: 'home', label: 'Dashboard', icon: Icons.home },
  { id: 'storyboard', label: 'Storyboard', icon: Icons.fileText },
  { id: 'projects', label: 'Projects', icon: Icons.folder },
  { id: 'settings', label: 'Settings', icon: Icons.settings },
];

export default function Home() {
  const [page, setPage] = useState<Page>('home');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0a0a0f' }}>
      {/* Sidebar */}
      <aside style={{
        width: '260px',
        background: 'linear-gradient(180deg, #0f0f15 0%, #0a0a10 100%)',
        borderRight: '1px solid rgba(255,255,255,0.06)',
        padding: '24px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}>
        {/* Logo */}
        <div style={{ 
          padding: '0 16px 24px', 
          borderBottom: '1px solid rgba(255,255,255,0.06)', 
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #5b8def 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '18px',
            fontWeight: 700,
            color: 'white',
          }}>P</div>
          <div>
            <h1 style={{ fontSize: '16px', fontWeight: 700, color: '#fff', letterSpacing: '-0.02em' }}>
              PPT Master
            </h1>
            <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '2px' }}>
              AI Storyboard Generator
            </p>
          </div>
        </div>

        {/* Nav Items */}
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setPage(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 16px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              background: page === item.id ? 'rgba(91, 141, 239, 0.12)' : 'transparent',
              color: page === item.id ? '#5b8def' : 'rgba(255,255,255,0.5)',
              fontSize: '14px',
              fontWeight: page === item.id ? 600 : 400,
              textAlign: 'left',
              width: '100%',
            }}
          >
            <span style={{ opacity: page === item.id ? 1 : 0.6 }}>{item.icon}</span>
            <span>{item.label}</span>
            {page === item.id && (
              <div style={{
                marginLeft: 'auto',
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: '#5b8def',
              }} />
            )}
          </button>
        ))}

        {/* Bottom section */}
        <div style={{ 
          marginTop: 'auto', 
          padding: '16px', 
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}>
          <div style={{
            background: 'rgba(91, 141, 239, 0.08)',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '12px',
          }}>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginBottom: '4px' }}>
              LLM Status
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: '#22c55e',
              }} />
              <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>
                Gemma4 (Ollama)
              </span>
            </div>
          </div>
          <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', textAlign: 'center' }}>
            v2.5.0
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ 
        flex: 1, 
        padding: '32px 40px', 
        overflowY: 'auto',
        background: '#0a0a0f',
      }}>
        {page === 'home' && <HomePage onNavigate={setPage} />}
        {page === 'storyboard' && <StoryboardPage />}
        {page === 'projects' && <ProjectsPage />}
        {page === 'settings' && <SettingsPage />}
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────
// Shared Styles
// ─────────────────────────────────────────────

const cardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.03)',
  backdropFilter: 'blur(20px)',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: '12px',
  padding: '24px',
  transition: 'all 0.2s ease',
};

const inputStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '8px',
  padding: '10px 14px',
  color: '#fff',
  width: '100%',
  fontSize: '14px',
  outline: 'none',
  transition: 'border-color 0.2s',
};

const btnPrimaryStyle: React.CSSProperties = {
  background: 'linear-gradient(135deg, #5b8def 0%, #8b5cf6 100%)',
  color: 'white',
  padding: '10px 24px',
  borderRadius: '8px',
  fontWeight: 600,
  fontSize: '14px',
  border: 'none',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
};

const btnSecondaryStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.04)',
  color: 'rgba(255,255,255,0.7)',
  padding: '10px 20px',
  borderRadius: '8px',
  fontWeight: 500,
  fontSize: '13px',
  border: '1px solid rgba(255,255,255,0.08)',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
};

// ─────────────────────────────────────────────
// Home Page
// ─────────────────────────────────────────────

function HomePage({ onNavigate }: { onNavigate: (p: Page) => void }) {
  return (
    <div>
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ 
          fontSize: '28px', 
          fontWeight: 700, 
          marginBottom: '8px',
          background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.02em',
        }}>
          Welcome back
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '15px' }}>
          Transform documents into structured storyboards with AI
        </p>
      </div>

      {/* Action Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '40px' }}>
        <div 
          style={{ ...cardStyle, cursor: 'pointer' }}
          onClick={() => onNavigate('storyboard')}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(91,141,239,0.3)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          <div style={{ 
            width: '40px', height: '40px', borderRadius: '10px',
            background: 'rgba(91,141,239,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px', color: '#5b8def',
          }}>
            {Icons.fileText}
          </div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
            Create Storyboard
          </h3>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', lineHeight: '1.5' }}>
            Upload Word/PPT/PDF → AI extracts key info → Export structured Word/PDF
          </p>
        </div>

        <div 
          style={{ ...cardStyle, cursor: 'pointer' }}
          onClick={() => onNavigate('projects')}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(91,141,239,0.3)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          <div style={{ 
            width: '40px', height: '40px', borderRadius: '10px',
            background: 'rgba(139,92,246,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px', color: '#8b5cf6',
          }}>
            {Icons.folder}
          </div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
            Manage Projects
          </h3>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', lineHeight: '1.5' }}>
            View, manage, and export generated PPT projects
          </p>
        </div>

        <div 
          style={{ ...cardStyle, cursor: 'pointer' }}
          onClick={() => onNavigate('settings')}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'rgba(91,141,239,0.3)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          <div style={{ 
            width: '40px', height: '40px', borderRadius: '10px',
            background: 'rgba(34,197,94,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px', color: '#22c55e',
          }}>
            {Icons.settings}
          </div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', marginBottom: '6px' }}>
            Configuration
          </h3>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', lineHeight: '1.5' }}>
            Configure LLM (Gemma4/Ollama), API keys, language
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'rgba(255,255,255,0.5)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Quick Info
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        {[
          { label: 'Default LLM', value: 'Gemma4', icon: Icons.cpu, color: '#5b8def' },
          { label: 'Language', value: 'Vietnamese', icon: Icons.globe, color: '#8b5cf6' },
          { label: 'Output Format', value: 'Word / PDF', icon: Icons.file, color: '#22c55e' },
          { label: 'Image Source', value: 'Web Search', icon: Icons.search, color: '#f59e0b' },
        ].map((stat) => (
          <div key={stat.label} style={{
            ...cardStyle,
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: '8px',
              background: `${stat.color}15`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: stat.color, flexShrink: 0,
            }}>
              {stat.icon}
            </div>
            <div>
              <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.3)', marginBottom: '2px' }}>
                {stat.label}
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>
                {stat.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Storyboard Page
// ─────────────────────────────────────────────

function StoryboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState('vi');
  const [outputFormat, setOutputFormat] = useState('docx');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [previewName, setPreviewName] = useState<string>('');
  const [showPreview, setShowPreview] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  }, []);

  const handleGenerate = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setPreview(null);
    setShowPreview(false);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', language);
    formData.append('output_format', outputFormat);

    try {
      const response = await fetch('/api/storyboard/generate', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        // Get filename from Content-Disposition header
        const disposition = response.headers.get('Content-Disposition');
        let filename = `storyboard.${outputFormat}`;
        if (disposition) {
          const match = disposition.match(/filename=(.+)/);
          if (match) filename = match[1].replace(/"/g, '');
        }
        
        // Store blob for preview and download
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Fetch preview from projects
        const projectName = file.name.replace(/\.[^.]+$/, '');
        try {
          const previewRes = await fetch(`/api/projects/${encodeURIComponent(projectName)}/preview`);
          if (previewRes.ok) {
            const data = await previewRes.json();
            setPreview(data.content);
            setPreviewName(filename);
            setShowPreview(true);
          }
        } catch {
          // If preview fails, just download
        }
        
        // Store download URL
        setResult({
          type: 'success',
          message: `Storyboard created: ${filename}`
        });
        
        // Store for download button
        (window as any).__storyboardUrl = url;
        (window as any).__storyboardFilename = filename;
      } else {
        const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
        setResult({ type: 'error', message: err.detail || 'Failed to create storyboard' });
      }
    } catch (err: any) {
      setResult({ type: 'error', message: `Connection error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const url = (window as any).__storyboardUrl;
    const filename = (window as any).__storyboardFilename;
    if (url) {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
    }
  };

  return (
    <div>
      <h2 style={{ 
        fontSize: '28px', fontWeight: 700, marginBottom: '8px',
        background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      }}>
        Create Storyboard
      </h2>
      <p style={{ color: 'rgba(255,255,255,0.4)', marginBottom: '32px', fontSize: '14px' }}>
        Upload a document → AI extracts key information → Export structured storyboard
      </p>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input')?.click()}
        style={{
          border: `2px dashed ${dragging ? '#5b8def' : 'rgba(255,255,255,0.08)'}`,
          borderRadius: '12px',
          padding: '48px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          background: dragging ? 'rgba(91,141,239,0.05)' : 'rgba(255,255,255,0.02)',
          marginBottom: '24px',
        }}
      >
        <input
          id="file-input"
          type="file"
          accept=".docx,.doc,.pptx,.pdf,.xlsx"
          style={{ display: 'none' }}
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file ? (
          <div>
            <div style={{ color: '#5b8def', marginBottom: '12px' }}>{Icons.file}</div>
            <div style={{ fontWeight: 600, color: '#fff', fontSize: '15px' }}>{file.name}</div>
            <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', marginTop: '4px' }}>
              {(file.size / 1024 / 1024).toFixed(2)} MB — Click to change
            </div>
          </div>
        ) : (
          <div>
            <div style={{ color: 'rgba(255,255,255,0.3)', marginBottom: '16px' }}>{Icons.upload}</div>
            <div style={{ fontWeight: 600, color: '#fff', marginBottom: '4px', fontSize: '15px' }}>
              Drag & drop file here
            </div>
            <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: '13px' }}>
              Supports: DOCX, DOC, PPTX, PDF, XLSX
            </div>
          </div>
        )}
      </div>

      {/* Options */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
            Output Language
          </label>
          <select
            style={inputStyle}
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option value="vi">Vietnamese</option>
            <option value="en">English</option>
            <option value="zh">Chinese</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
            Output Format
          </label>
          <select
            style={inputStyle}
            value={outputFormat}
            onChange={(e) => setOutputFormat(e.target.value)}
          >
            <option value="docx">Word (.docx)</option>
            <option value="pdf">PDF (.pdf)</option>
          </select>
        </div>
      </div>

      {/* Generate Button */}
      <button
        style={{
          ...btnPrimaryStyle,
          width: '100%',
          padding: '14px',
          fontSize: '15px',
          justifyContent: 'center',
          opacity: (!file || loading) ? 0.5 : 1,
          cursor: (!file || loading) ? 'not-allowed' : 'pointer',
        }}
        onClick={handleGenerate}
        disabled={!file || loading}
      >
        {loading ? (
          <>
            <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⏳</span>
            Generating storyboard...
          </>
        ) : (
          <>
            {Icons.zap}
            Generate Storyboard
          </>
        )}
      </button>

      {/* Result */}
      {result && (
        <div style={{
          ...cardStyle,
          marginTop: '24px',
          borderColor: result.type === 'success' ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)',
          background: result.type === 'success' ? 'rgba(34,197,94,0.05)' : 'rgba(239,68,68,0.05)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <div style={{ color: result.type === 'success' ? '#22c55e' : '#ef4444' }}>
            {result.type === 'success' ? Icons.check : '⚠️'}
          </div>
          <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px', flex: 1 }}>
            {result.message}
          </span>
          {result.type === 'success' && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button style={btnSecondaryStyle} onClick={() => setShowPreview(!showPreview)}>
                {showPreview ? 'Hide Preview' : 'Preview'}
              </button>
              <button style={btnPrimaryStyle} onClick={handleDownload}>
                {Icons.download} Download
              </button>
            </div>
          )}
        </div>
      )}

      {/* Preview Panel */}
      {showPreview && preview && (
        <div style={{
          ...cardStyle,
          marginTop: '16px',
          maxHeight: '500px',
          overflowY: 'auto',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff' }}>
              Preview: {previewName}
            </h3>
            <button style={btnSecondaryStyle} onClick={handleDownload}>
              {Icons.download} Download
            </button>
          </div>
          <div style={{
            background: 'rgba(255,255,255,0.02)',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <MarkdownRenderer content={preview} />
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Projects Page
// ─────────────────────────────────────────────

function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewProject, setPreviewProject] = useState<any>(null);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/projects');
      const data = await res.json();
      setProjects(data.projects || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteProject = async (name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    try {
      await fetch(`/api/projects/${encodeURIComponent(name)}`, { method: 'DELETE' });
      loadProjects();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const downloadFile = (projectName: string, filename: string) => {
    window.open(`/api/projects/${encodeURIComponent(projectName)}/download/${encodeURIComponent(filename)}`);
  };

  const previewStoryboard = async (name: string) => {
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(name)}/preview`);
      if (res.ok) {
        const data = await res.json();
        setPreviewProject(data);
      }
    } catch (err) {
      console.error('Failed to load preview:', err);
    }
  };

  // Load on mount
  useState(() => { loadProjects(); });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h2 style={{
            fontSize: '28px', fontWeight: 700,
            background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>Projects</h2>
          <p style={{ color: 'rgba(255,255,255,0.4)', marginTop: '4px', fontSize: '14px' }}>
            History of generated storyboards and PPTs
          </p>
        </div>
        <button style={btnSecondaryStyle} onClick={loadProjects}>
          {Icons.refresh} Refresh
        </button>
      </div>

      {projects.length === 0 ? (
        <div style={{ ...cardStyle, padding: '64px', textAlign: 'center' }}>
          <div style={{ color: 'rgba(255,255,255,0.2)', marginBottom: '16px' }}>{Icons.folder}</div>
          <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '14px' }}>
            No projects yet. Create a Storyboard first.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {projects.map((p) => (
            <div key={p.name} style={{ ...cardStyle, display: 'flex', alignItems: 'center', gap: '16px' }}>
              {/* Icon */}
              <div style={{
                width: '44px', height: '44px', borderRadius: '10px', flexShrink: 0,
                background: p.has_storyboard ? 'rgba(91,141,239,0.12)' : 'rgba(139,92,246,0.12)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: p.has_storyboard ? '#5b8def' : '#8b5cf6',
              }}>
                {p.has_storyboard ? Icons.fileText : Icons.folder}
              </div>

              {/* Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ fontWeight: 600, color: '#fff', fontSize: '14px', marginBottom: '4px' }}>
                  {p.name}
                </h3>
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>
                  {p.source_file && <span>Source: {p.source_file}</span>}
                  {p.created_at && <span>{new Date(p.created_at).toLocaleDateString()}</span>}
                  {p.language && <span>Lang: {p.language.toUpperCase()}</span>}
                  {p.output_files?.length > 0 && (
                    <span>{p.output_files[0].name} ({(p.output_files[0].size / 1024).toFixed(0)}KB)</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                {p.has_storyboard && (
                  <button
                    style={{ ...btnSecondaryStyle, padding: '8px 12px', fontSize: '12px' }}
                    onClick={() => previewStoryboard(p.name)}
                    title="Preview"
                  >
                    {Icons.fileText} Preview
                  </button>
                )}
                {p.output_files?.map((f: any) => (
                  <button
                    key={f.name}
                    style={{ ...btnPrimaryStyle, padding: '8px 12px', fontSize: '12px' }}
                    onClick={() => downloadFile(p.name, f.name)}
                    title={`Download ${f.name}`}
                  >
                    {Icons.download} Download
                  </button>
                ))}
                <button
                  style={{ ...btnSecondaryStyle, padding: '8px 12px', fontSize: '12px', borderColor: 'rgba(239,68,68,0.3)', color: '#ef4444' }}
                  onClick={() => deleteProject(p.name)}
                  title="Delete"
                >
                  ✕ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewProject && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '40px',
        }} onClick={() => setPreviewProject(null)}>
          <div style={{
            ...cardStyle,
            maxWidth: '800px', width: '100%', maxHeight: '80vh',
            overflowY: 'auto', padding: '32px',
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#fff' }}>
                {previewProject.name}
              </h3>
              <button style={btnSecondaryStyle} onClick={() => setPreviewProject(null)}>✕ Close</button>
            </div>
            <div>
              <MarkdownRenderer content={previewProject.content || ''} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Settings Page
// ─────────────────────────────────────────────

function SettingsPage() {
  const [settings, setSettings] = useState<any>({
    llm: { provider: 'ollama', model: 'gemma4:8b', endpoint: 'http://localhost:11434', api_key: '' },
    image_search: { pexels_api_key: '', pixabay_api_key: '' },
    tts: { provider: 'edge-tts', voice: 'vi-VN-HoaiMyNeural' },
    language: 'vi',
  });
  const [saved, setSaved] = useState(false);

  const saveSettings = async () => {
    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save settings:', err);
    }
  };

  return (
    <div>
      <h2 style={{ 
        fontSize: '28px', fontWeight: 700, marginBottom: '8px',
        background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      }}>Settings</h2>
      <p style={{ color: 'rgba(255,255,255,0.4)', marginBottom: '32px', fontSize: '14px' }}>
        Configure LLM, API keys, language, and other options
      </p>

      {/* LLM Settings */}
      <div style={{ ...cardStyle, marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <div style={{ color: '#5b8def' }}>{Icons.cpu}</div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff' }}>LLM Configuration</h3>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
              Provider
            </label>
            <select
              style={inputStyle}
              value={settings.llm?.provider || 'ollama'}
              onChange={(e) => setSettings({ ...settings, llm: { ...settings.llm, provider: e.target.value } })}
            >
              <option value="ollama">Ollama (Local — Gemma4)</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="claude">Claude (Anthropic)</option>
              <option value="gemini">Gemini (Google)</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
              Model
            </label>
            <input
              style={inputStyle}
              value={settings.llm?.model || 'gemma4:8b'}
              onChange={(e) => setSettings({ ...settings, llm: { ...settings.llm, model: e.target.value } })}
              placeholder="gemma4:8b"
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
              Endpoint
            </label>
            <input
              style={inputStyle}
              value={settings.llm?.endpoint || 'http://localhost:11434'}
              onChange={(e) => setSettings({ ...settings, llm: { ...settings.llm, endpoint: e.target.value } })}
              placeholder="http://localhost:11434"
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
              API Key (cloud providers only)
            </label>
            <input
              style={inputStyle}
              type="password"
              value={settings.llm?.api_key || ''}
              onChange={(e) => setSettings({ ...settings, llm: { ...settings.llm, api_key: e.target.value } })}
              placeholder="sk-..."
            />
          </div>
        </div>
      </div>

      {/* Image Search */}
      <div style={{ ...cardStyle, marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <div style={{ color: '#f59e0b' }}>{Icons.search}</div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff' }}>Image Search</h3>
        </div>
        <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', marginBottom: '16px' }}>
          Search images from web (Openverse & Wikimedia free, no API key needed)
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
              Pexels API Key (optional)
            </label>
            <input
              style={inputStyle}
              type="password"
              value={settings.image_search?.pexels_api_key || ''}
              onChange={(e) => setSettings({
                ...settings,
                image_search: { ...settings.image_search, pexels_api_key: e.target.value }
              })}
              placeholder="Pexels API key"
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginBottom: '6px', fontWeight: 500 }}>
              Pixabay API Key (optional)
            </label>
            <input
              style={inputStyle}
              type="password"
              value={settings.image_search?.pixabay_api_key || ''}
              onChange={(e) => setSettings({
                ...settings,
                image_search: { ...settings.image_search, pixabay_api_key: e.target.value }
              })}
              placeholder="Pixabay API key"
            />
          </div>
        </div>
      </div>

      {/* Language */}
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <div style={{ color: '#8b5cf6' }}>{Icons.globe}</div>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff' }}>Language</h3>
        </div>
        <select
          style={{ ...inputStyle, maxWidth: '300px' }}
          value={settings.language || 'vi'}
          onChange={(e) => setSettings({ ...settings, language: e.target.value })}
        >
          <option value="vi">Vietnamese</option>
          <option value="en">English</option>
          <option value="zh">Chinese</option>
        </select>
      </div>

      {/* Save Button */}
      <button style={btnPrimaryStyle} onClick={saveSettings}>
        {saved ? Icons.check : Icons.download}
        {saved ? 'Saved!' : 'Save Settings'}
      </button>
    </div>
  );
}
