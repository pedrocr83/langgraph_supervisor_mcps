import { useLanguageStore } from '../context/languageStore'

function LanguageSwitcher({ style = {} }) {
  const language = useLanguageStore((state) => state.language)
  const setLanguage = useLanguageStore((state) => state.setLanguage)

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      backgroundColor: 'var(--bg-tertiary)',
      borderRadius: '8px',
      padding: '4px',
      border: '1px solid var(--border-color)',
      ...style
    }}>
      <button
        onClick={() => setLanguage('pt')}
        style={{
          padding: '6px 12px',
          borderRadius: '6px',
          border: 'none',
          backgroundColor: language === 'pt' ? 'var(--accent-color)' : 'transparent',
          color: language === 'pt' ? 'white' : 'var(--text-secondary)',
          fontSize: '13px',
          fontWeight: language === 'pt' ? '600' : '400',
          cursor: 'pointer',
          transition: 'all 0.2s',
          fontFamily: 'inherit'
        }}
        onMouseEnter={(e) => {
          if (language !== 'pt') {
            e.target.style.backgroundColor = 'var(--bg-hover)'
            e.target.style.color = 'var(--text-primary)'
          }
        }}
        onMouseLeave={(e) => {
          if (language !== 'pt') {
            e.target.style.backgroundColor = 'transparent'
            e.target.style.color = 'var(--text-secondary)'
          }
        }}
      >
        PT
      </button>
      <button
        onClick={() => setLanguage('en')}
        style={{
          padding: '6px 12px',
          borderRadius: '6px',
          border: 'none',
          backgroundColor: language === 'en' ? 'var(--accent-color)' : 'transparent',
          color: language === 'en' ? 'white' : 'var(--text-secondary)',
          fontSize: '13px',
          fontWeight: language === 'en' ? '600' : '400',
          cursor: 'pointer',
          transition: 'all 0.2s',
          fontFamily: 'inherit'
        }}
        onMouseEnter={(e) => {
          if (language !== 'en') {
            e.target.style.backgroundColor = 'var(--bg-hover)'
            e.target.style.color = 'var(--text-primary)'
          }
        }}
        onMouseLeave={(e) => {
          if (language !== 'en') {
            e.target.style.backgroundColor = 'transparent'
            e.target.style.color = 'var(--text-secondary)'
          }
        }}
      >
        EN
      </button>
    </div>
  )
}

export default LanguageSwitcher

