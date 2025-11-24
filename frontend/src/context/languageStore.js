import { create } from 'zustand'

const translations = {
  pt: {
    // Login & Register
    login: {
      title: 'misteriosAI',
      subtitle: 'O seu assistente inteligente para Misterios Lda',
      whatIs: 'O que é o misteriosAI?',
      description: 'O misteriosAI é um assistente pessoal inteligente alimentado por tecnologia de IA avançada. Ajuda-o a aceder e gerir dados da empresa através de capacidades especializadas:',
      capabilities: {
        erp: 'Acesso ao Primavera ERP: Consultar vendas, inventário, finanças e dados empresariais',
        files: 'Gestão de Ficheiros: Pesquisar e aceder a documentos do SharePoint/OneDrive',
        realtime: 'Assistência em Tempo Real: Obter respostas instantâneas com respostas em streaming'
      },
      email: 'Endereço de email',
      password: 'Palavra-passe',
      confirmPassword: 'Confirmar Palavra-passe',
      passwordMin: 'Palavra-passe (mín. 8 caracteres)',
      signIn: 'Iniciar Sessão',
      signingIn: 'A iniciar sessão...',
      createAccount: 'Criar Conta',
      creatingAccount: 'A criar conta...',
      alreadyHaveAccount: 'Já tem uma conta? Iniciar sessão',
      noAccount: 'Não tem uma conta? Registar',
      passwordsNoMatch: 'As palavras-passe não coincidem',
      passwordTooShort: 'A palavra-passe deve ter pelo menos 8 caracteres'
    },
    // Chat
    chat: {
      startConversation: 'Inicie uma conversa com o misteriosAI',
      askAnything: 'Pergunte-me qualquer coisa!',
      tool: 'Ferramenta',
      thinking: 'O misteriosAI está a pensar',
      communicating: 'A comunicar com',
      callingTool: 'A chamar ferramenta',
      sendMessage: 'Enviar uma mensagem...',
      sending: 'A enviar...',
      send: 'Enviar',
      error: 'Erro',
      deleteFailed: 'Falha ao eliminar conversa'
    },
    // Sidebar
    sidebar: {
      newChat: 'Nova conversa',
      noConversations: 'Ainda não há conversas',
      newConversation: 'Nova conversa',
      deleteConversation: 'Eliminar conversa',
      logout: 'Terminar sessão',
      today: 'Hoje',
      yesterday: 'Ontem',
      daysAgo: 'Há {days} dias'
    }
  },
  en: {
    // Login & Register
    login: {
      title: 'misteriosAI',
      subtitle: 'Your intelligent assistant for Misterios Lda',
      whatIs: 'What is misteriosAI?',
      description: 'misteriosAI is an intelligent personal assistant powered by advanced AI technology. It helps you access and manage company data through specialized capabilities:',
      capabilities: {
        erp: 'Primavera ERP Access: Query sales, inventory, finance, and business data',
        files: 'File Management: Search and access documents from SharePoint/OneDrive',
        realtime: 'Real-time Assistance: Get instant answers with streaming responses'
      },
      email: 'Email address',
      password: 'Password',
      confirmPassword: 'Confirm Password',
      passwordMin: 'Password (min. 8 characters)',
      signIn: 'Sign in',
      signingIn: 'Signing in...',
      createAccount: 'Create Account',
      creatingAccount: 'Creating account...',
      alreadyHaveAccount: 'Already have an account? Sign in',
      noAccount: "Don't have an account? Register",
      passwordsNoMatch: 'Passwords do not match',
      passwordTooShort: 'Password must be at least 8 characters'
    },
    // Chat
    chat: {
      startConversation: 'Start a conversation with misteriosAI',
      askAnything: 'Ask me anything!',
      tool: 'Tool',
      thinking: 'misteriosAI is thinking',
      communicating: 'Communicating with',
      callingTool: 'Calling tool',
      sendMessage: 'Send a message...',
      sending: 'Sending...',
      send: 'Send',
      error: 'Error',
      deleteFailed: 'Failed to delete conversation'
    },
    // Sidebar
    sidebar: {
      newChat: 'New chat',
      noConversations: 'No conversations yet',
      newConversation: 'New conversation',
      deleteConversation: 'Delete conversation',
      logout: 'Logout',
      today: 'Today',
      yesterday: 'Yesterday',
      daysAgo: '{days} days ago'
    }
  }
}

export const useLanguageStore = create((set, get) => {
  // Get language from localStorage or default to Portuguese
  const getLanguage = () => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('language')
      return saved || 'pt'
    }
    return 'pt'
  }

  const currentLanguage = getLanguage()

  return {
    language: currentLanguage,
    getTranslations: () => translations[get().language],
    t: (key) => {
      const keys = key.split('.')
      const lang = get().language
      let value = translations[lang]
      for (const k of keys) {
        value = value?.[k]
      }
      return value || key
    },
    setLanguage: (lang) => {
      if (typeof window !== 'undefined') {
        localStorage.setItem('language', lang)
      }
      set({ language: lang })
    },
    toggleLanguage: () => {
      const newLang = get().language === 'pt' ? 'en' : 'pt'
      get().setLanguage(newLang)
    }
  }
})

