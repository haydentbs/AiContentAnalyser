import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { AlertCircle, Home } from 'lucide-react'

const NotFoundPage = () => {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-6 max-w-md">
        <AlertCircle className="w-16 h-16 text-orange-500 mx-auto" />
        <h1 className="text-4xl font-bold">Page Not Found</h1>
        <p className="text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/">
          <Button className="gap-2">
            <Home className="w-4 h-4" />
            Return Home
          </Button>
        </Link>
      </div>
    </div>
  )
}

export default NotFoundPage