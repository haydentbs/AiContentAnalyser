const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t py-6">
      <div className="container mx-auto px-4 text-center text-sm text-gray-500">
        <p>Content Scorecard &copy; {new Date().getFullYear()}</p>
        <p className="mt-1">A tool for evaluating and improving content quality</p>
      </div>
    </footer>
  )
}

export default Footer