
export default function TitleHeaderDashboard({ title, subtitle }) {
  return (
    <div className="mb-5">
        <h1 className="font-serif text-3xl font-semibold">{title}</h1>
        <span className="text-gray-600">{subtitle}</span>
    </div>
  )
}