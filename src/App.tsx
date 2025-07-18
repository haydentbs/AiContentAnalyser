import { Routes, Route } from 'react-router-dom'
import { Toaster } from './components/ui/toaster'
import MainLayout from './layouts/MainLayout'
import React, { lazy, Suspense } from 'react'

const HomePage = lazy(() => import('./pages/HomePage'))
const AnalyzePage = lazy(() => import('./pages/AnalyzePage'))
const ResultsPage = lazy(() => import('./pages/ResultsPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function App() {
  return (
    <>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="analyze" element={<AnalyzePage />} />
            <Route path="results/:reportId" element={<ResultsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
      <Toaster />
    </>
  )
}

export default App