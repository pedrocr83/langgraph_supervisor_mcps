import { useState } from 'react'
import { useLanguageStore } from '../context/languageStore'

function Sidebar({
    conversations,
    activeConversationId,
    onSelectConversation,
    onNewChat,
    onDeleteConversation,
    onLogout
}) {
    const [hoveredChatId, setHoveredChatId] = useState(null)
    const t = useLanguageStore((state) => state.t)
    const language = useLanguageStore((state) => state.language)

    const formatDate = (dateString) => {
        const date = new Date(dateString)
        const now = new Date()
        const diff = now - date
        const days = Math.floor(diff / (1000 * 60 * 60 * 24))

        if (days === 0) return t('sidebar.today')
        if (days === 1) return t('sidebar.yesterday')
        if (days < 7) {
            const daysAgo = t('sidebar.daysAgo')
            return daysAgo.replace('{days}', days)
        }
        return date.toLocaleDateString(language === 'pt' ? 'pt-PT' : 'en-US')
    }

    return (
        <div
            className="flex flex-col h-full"
            style={{
                width: '260px',
                backgroundColor: 'var(--bg-sidebar)',
                borderRight: '1px solid var(--border-color)',
            }}
        >
            {/* Header with New Chat button */}
            <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
                <button
                    onClick={onNewChat}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: 'var(--bg-tertiary)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--bg-hover)'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--bg-tertiary)'}
                >
                    <span style={{ fontSize: '18px' }}>+</span>
                    {t('sidebar.newChat')}
                </button>
            </div>

            {/* Chat History */}
            <div
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '8px',
                }}
            >
                {conversations.length === 0 ? (
                    <div style={{
                        padding: '16px',
                        textAlign: 'center',
                        color: 'var(--text-muted)',
                        fontSize: '14px'
                    }}>
                        {t('sidebar.noConversations')}
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {conversations.map((conv) => (
                            <div
                                key={conv.id}
                                onClick={() => onSelectConversation(conv.id)}
                                onMouseEnter={() => setHoveredChatId(conv.id)}
                                onMouseLeave={() => setHoveredChatId(null)}
                                style={{
                                    padding: '12px',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    backgroundColor: activeConversationId === conv.id
                                        ? 'var(--bg-tertiary)'
                                        : hoveredChatId === conv.id
                                            ? 'var(--bg-hover)'
                                            : 'transparent',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    gap: '8px',
                                    transition: 'background-color 0.15s ease',
                                }}
                            >
                                <div style={{ flex: 1, overflow: 'hidden' }}>
                                    <div style={{
                                        fontSize: '14px',
                                        color: 'var(--text-primary)',
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        fontWeight: activeConversationId === conv.id ? '500' : '400',
                                    }}>
                                        {conv.title || t('sidebar.newConversation')}
                                    </div>
                                    <div style={{
                                        fontSize: '12px',
                                        color: 'var(--text-muted)',
                                        marginTop: '2px',
                                    }}>
                                        {formatDate(conv.updated_at || conv.created_at)}
                                    </div>
                                </div>

                                {/* Delete button - only show on hover */}
                                {hoveredChatId === conv.id && (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            onDeleteConversation(conv.id)
                                        }}
                                        style={{
                                            padding: '6px',
                                            backgroundColor: 'transparent',
                                            border: 'none',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'var(--text-muted)',
                                        }}
                                        onMouseEnter={(e) => {
                                            e.target.style.backgroundColor = 'var(--danger-color)'
                                            e.target.style.color = 'white'
                                        }}
                                        onMouseLeave={(e) => {
                                            e.target.style.backgroundColor = 'transparent'
                                            e.target.style.color = 'var(--text-muted)'
                                        }}
                                        title={t('sidebar.deleteConversation')}
                                    >
                                        🗑️
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer with Logout */}
            <div style={{
                padding: '16px',
                borderTop: '1px solid var(--border-color)'
            }}>
                <button
                    onClick={onLogout}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: 'transparent',
                        color: 'var(--text-secondary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => {
                        e.target.style.backgroundColor = 'var(--bg-tertiary)'
                        e.target.style.color = 'var(--text-primary)'
                    }}
                    onMouseLeave={(e) => {
                        e.target.style.backgroundColor = 'transparent'
                        e.target.style.color = 'var(--text-secondary)'
                    }}
                >
                    {t('sidebar.logout')}
                </button>
            </div>
        </div>
    )
}

export default Sidebar
