import { Link } from 'react-router-dom'
import { FileText, Settings } from 'lucide-react'
import { Button } from './ui/button'

const Navbar = () => {
  return (
    <header className="bg-white border-b">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <FileText className="h-6 w-6" />
          <span className="font-bold text-xl">Content Scorecard</span>
        </Link>
        
        <nav className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
          <Link to="/analyze">
            <Button variant="ghost">Analyze Content</Button>
          </Link>
          <Link to="/settings">
            <Button variant="ghost" size="icon" aria-label="Settings">
              <Settings className="h-5 w-5" />
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  )
}

export default Navbar