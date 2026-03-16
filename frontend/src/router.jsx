import { createBrowserRouter } from "react-router-dom"


import HomePage from "./shared/components/HomePage" 
import LearningPage from "./modules/learning/pages/LearningPage"
import TradingPage from "./modules/trading/pages/TradingPage"
import PortfolioPage from "./modules/portfolio/pages/PortfolioPage"
import AIPage from "./modules/ai_engine/pages/AIPage"
import SimulationPage from "./modules/simulation/pages/SimulationPage"
import LoginPage from "./modules/users/pages/LoginPage"

const router = createBrowserRouter([
  { path: "/",          element: <HomePage /> },
  { path: "/login",     element: <LoginPage /> },
  { path: "/learning",  element: <LearningPage /> },
  { path: "/trading",   element: <TradingPage /> },
  { path: "/portfolio", element: <PortfolioPage /> },
  { path: "/ai",        element: <AIPage /> },
  { path: "/simulation",element: <SimulationPage /> },
])

export default router
