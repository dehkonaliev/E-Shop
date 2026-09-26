import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="container page narrow">
      <div className="empty-panel">
        <p className="eyebrow">404</p>
        <h1 className="headline">This page does not exist</h1>
        <p className="muted">
          The link may be out of date, or the item you are looking for has been retired.
        </p>
        <Link className="btn btn-dark" to="/">
          Back to home
        </Link>
      </div>
    </div>
  )
}
