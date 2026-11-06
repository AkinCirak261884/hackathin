import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './styles.css'
import './theme.css' // visual layer, see file header

createRoot(document.getElementById('root')).render(<App />)
