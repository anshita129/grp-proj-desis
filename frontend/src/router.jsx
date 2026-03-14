import { createBrowserRouter } from "react-router-dom"

import LearningPage from "./modules/learning/pages/LearningPage"
import ModulePage from "./modules/learning/pages/ModulePage"
import QuizPage from "./modules/learning/pages/QuizPage"
import ResultsPage from "./modules/learning/pages/ResultsPage"
import BadgesPage from "./modules/learning/pages/BadgesPage"
import TradingPage from "./modules/trading/pages/TradingPage"
import PortfolioPage from "./modules/portfolio/pages/PortfolioPage"
import AIPage from "./modules/ai_engine/pages/AIPage"
import SimulationPage from "./modules/simulation/pages/SimulationPage"
import LoginPage from "./modules/users/pages/LoginPage"

import AppShell from "./AppShell"

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <div className="p-8 text-2xl">Home — GRP DESIS</div> },
      { path: "learning", element: <LearningPage /> },
      { path: "learning/badges", element: <BadgesPage /> },
      { path: "learning/results/:attemptId", element: <ResultsPage /> },
      { path: "learning/:slug", element: <ModulePage /> },
      { path: "learning/:slug/quiz", element: <QuizPage /> },
      { path: "trading", element: <TradingPage /> },
      { path: "portfolio", element: <PortfolioPage /> },
      { path: "ai", element: <AIPage /> },
      { path: "simulation", element: <SimulationPage /> },
    ]
  },
  { path: "/login", element: <LoginPage /> },
])

export default router
