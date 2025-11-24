import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function MarkdownRenderer({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // Style headings
        h1: ({ node, ...props }) => (
          <h1 style={{
            fontSize: '24px',
            fontWeight: '700',
            marginTop: '16px',
            marginBottom: '12px',
            color: 'var(--text-primary)',
            lineHeight: '1.4',
          }} {...props} />
        ),
        h2: ({ node, ...props }) => (
          <h2 style={{
            fontSize: '20px',
            fontWeight: '600',
            marginTop: '14px',
            marginBottom: '10px',
            color: 'var(--text-primary)',
            lineHeight: '1.4',
          }} {...props} />
        ),
        h3: ({ node, ...props }) => (
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            marginTop: '12px',
            marginBottom: '8px',
            color: 'var(--text-primary)',
            lineHeight: '1.4',
          }} {...props} />
        ),
        // Style paragraphs
        p: ({ node, ...props }) => (
          <p style={{
            marginTop: '8px',
            marginBottom: '8px',
            lineHeight: '1.6',
            color: 'var(--text-primary)',
          }} {...props} />
        ),
        // Style lists
        ul: ({ node, ...props }) => (
          <ul style={{
            marginTop: '8px',
            marginBottom: '8px',
            paddingLeft: '24px',
            lineHeight: '1.6',
            color: 'var(--text-primary)',
          }} {...props} />
        ),
        ol: ({ node, ...props }) => (
          <ol style={{
            marginTop: '8px',
            marginBottom: '8px',
            paddingLeft: '24px',
            lineHeight: '1.6',
            color: 'var(--text-primary)',
          }} {...props} />
        ),
        li: ({ node, ...props }) => (
          <li style={{
            marginTop: '4px',
            marginBottom: '4px',
            lineHeight: '1.6',
            color: 'var(--text-primary)',
          }} {...props} />
        ),
        // Style code blocks
        code: ({ node, inline, className, children, ...props }) => {
          if (inline) {
            return (
              <code style={{
                backgroundColor: 'var(--bg-tertiary)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'monospace',
                color: 'var(--accent-color)',
              }} {...props}>
                {children}
              </code>
            )
          }
          return (
            <code className={className} style={{
              display: 'block',
              backgroundColor: 'var(--bg-tertiary)',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '14px',
              fontFamily: 'monospace',
              overflowX: 'auto',
              marginTop: '8px',
              marginBottom: '8px',
              lineHeight: '1.5',
              color: 'var(--text-primary)',
            }} {...props}>
              {children}
            </code>
          )
        },
        pre: ({ node, children, ...props }) => (
          <pre style={{
            backgroundColor: 'var(--bg-tertiary)',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '14px',
            fontFamily: 'monospace',
            overflowX: 'auto',
            marginTop: '8px',
            marginBottom: '8px',
            lineHeight: '1.5',
            color: 'var(--text-primary)',
          }} {...props}>
            {children}
          </pre>
        ),
        // Style tables
        table: ({ node, ...props }) => (
          <div style={{ overflowX: 'auto', marginTop: '12px', marginBottom: '12px' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px',
              lineHeight: '1.5',
            }} {...props} />
          </div>
        ),
        thead: ({ node, ...props }) => (
          <thead style={{
            backgroundColor: 'var(--bg-tertiary)',
          }} {...props} />
        ),
        tbody: ({ node, ...props }) => (
          <tbody {...props} />
        ),
        tr: ({ node, ...props }) => (
          <tr style={{
            borderBottom: '1px solid var(--border-color)',
          }} {...props} />
        ),
        th: ({ node, ...props }) => (
          <th style={{
            padding: '10px 12px',
            textAlign: 'left',
            fontWeight: '600',
            color: 'var(--text-primary)',
            borderRight: '1px solid var(--border-color)',
          }} {...props} />
        ),
        td: ({ node, ...props }) => (
          <td style={{
            padding: '10px 12px',
            color: 'var(--text-primary)',
            borderRight: '1px solid var(--border-color)',
          }} {...props} />
        ),
        // Style blockquotes
        blockquote: ({ node, ...props }) => (
          <blockquote style={{
            borderLeft: '4px solid var(--accent-color)',
            paddingLeft: '16px',
            marginTop: '8px',
            marginBottom: '8px',
            marginLeft: '0',
            color: 'var(--text-secondary)',
            fontStyle: 'italic',
          }} {...props} />
        ),
        // Style links
        a: ({ node, ...props }) => (
          <a style={{
            color: 'var(--accent-color)',
            textDecoration: 'underline',
            cursor: 'pointer',
          }} {...props} />
        ),
        // Style horizontal rules
        hr: ({ node, ...props }) => (
          <hr style={{
            border: 'none',
            borderTop: '1px solid var(--border-color)',
            marginTop: '16px',
            marginBottom: '16px',
          }} {...props} />
        ),
        // Style strong/bold
        strong: ({ node, ...props }) => (
          <strong style={{
            fontWeight: '600',
            color: 'var(--text-primary)',
          }} {...props} />
        ),
        // Style emphasis/italic
        em: ({ node, ...props }) => (
          <em style={{
            fontStyle: 'italic',
            color: 'var(--text-primary)',
          }} {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export default MarkdownRenderer

