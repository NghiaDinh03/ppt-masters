'use client';

import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

/**
 * Renders markdown content with proper table support, headers, bullets, etc.
 * Used in both StoryboardPage preview and ProjectsPage preview modal.
 */
export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let tableRows: string[][] = [];
  let i = 0;

  const flushTable = () => {
    if (tableRows.length > 0) {
      elements.push(renderTable(tableRows, elements.length));
      tableRows = [];
    }
  };

  while (i < lines.length) {
    const line = lines[i].trim();

    // Table detection
    if (line.startsWith('|') && line.endsWith('|')) {
      // Skip separator rows
      if (/^\|[\s\-:|]+\|$/.test(line)) {
        i++;
        continue;
      }
      const cells = line.split('|').slice(1, -1).map(c => c.trim());
      tableRows.push(cells);
      i++;
      continue;
    } else {
      flushTable();
    }

    if (line === '') {
      elements.push(<div key={`br-${i}`} style={{ height: '8px' }} />);
      i++;
      continue;
    }

    // Headers
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      elements.push(
        <h1 key={`h1-${i}`} style={{ fontSize: '20px', fontWeight: 700, color: '#fff', margin: '20px 0 10px', fontFamily: 'Times New Roman, serif' }}>
          {renderInline(line.slice(2))}
        </h1>
      );
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${i}`} style={{ fontSize: '17px', fontWeight: 600, color: '#5b8def', margin: '16px 0 8px', fontFamily: 'Times New Roman, serif' }}>
          {renderInline(line.slice(3))}
        </h2>
      );
      i++;
      continue;
    }
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${i}`} style={{ fontSize: '15px', fontWeight: 600, color: 'rgba(255,255,255,0.9)', margin: '12px 0 6px', fontFamily: 'Times New Roman, serif' }}>
          {renderInline(line.slice(4))}
        </h3>
      );
      i++;
      continue;
    }
    if (line.startsWith('#### ')) {
      elements.push(
        <h4 key={`h4-${i}`} style={{ fontSize: '13px', fontWeight: 600, color: 'rgba(255,255,255,0.8)', margin: '10px 0 4px', fontFamily: 'Times New Roman, serif' }}>
          {renderInline(line.slice(5))}
        </h4>
      );
      i++;
      continue;
    }

    // Bullets
    if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <div key={`li-${i}`} style={{ margin: '3px 0 3px 20px', fontSize: '13px', lineHeight: '1.6', fontFamily: 'Times New Roman, serif' }}>
          <span style={{ color: '#5b8def', marginRight: '8px' }}>•</span>
          {renderInline(line.slice(2))}
        </div>
      );
      i++;
      continue;
    }

    // Regular text
    elements.push(
      <p key={`p-${i}`} style={{ margin: '4px 0', fontSize: '13px', lineHeight: '1.6', fontFamily: 'Times New Roman, serif', color: 'rgba(255,255,255,0.7)' }}>
        {renderInline(line)}
      </p>
    );
    i++;
  }

  flushTable();

  return <>{elements}</>;
}

function renderInline(text: string): React.ReactNode {
  // Split by **bold** markers
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, j) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={j} style={{ color: '#5b8def', fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
    }
    return <span key={j}>{part}</span>;
  });
}

function renderTable(rows: string[][], key: number): React.ReactNode {
  if (rows.length === 0) return null;
  const numCols = Math.max(...rows.map(r => r.length));

  return (
    <div key={`table-${key}`} style={{ margin: '12px 0', overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '12px',
        fontFamily: 'Times New Roman, serif',
      }}>
        <thead>
          <tr>
            {Array.from({ length: numCols }, (_, j) => (
              <th key={j} style={{
                background: '#2c3e50',
                color: '#fff',
                padding: '8px 12px',
                textAlign: 'left',
                fontWeight: 600,
                borderBottom: '2px solid #1a252f',
                whiteSpace: 'nowrap',
              }}>
                {rows[0]?.[j] || ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(1).map((row, ri) => (
            <tr key={ri} style={{ background: ri % 2 === 0 ? 'rgba(255,255,255,0.03)' : 'transparent' }}>
              {Array.from({ length: numCols }, (_, ci) => (
                <td key={ci} style={{
                  padding: '6px 12px',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  color: 'rgba(255,255,255,0.7)',
                }}>
                  {renderInline(row[ci] || '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
