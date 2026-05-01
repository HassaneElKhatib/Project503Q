import { BsBarChartFill } from "react-icons/bs";

export default function Card( {title, amount, percentage, icon} ) {
  return (
    <div className="bg-white p-4 rounded-2xl shadow-lg">
        <div className="mb-2">
            <div className="flex justify-between items-center">
              <h2 className="font-semibold text-gray-600 font-serif">{title}</h2>
              <div className="p-2 bg-primary rounded-xl flex justify-center items-center">
                {icon}
              </div>
            </div>
            <span className="text-xl">{amount}</span>
        </div>
        {percentage && (
        <div className="flex items-center gap-2 mb-2">
          <BsBarChartFill size={12} className="opacity-20 text-green-800"/>
          <span className="text-xs text-green-600">{percentage} from last month</span>
        </div>
        )}
    </div>
  )
}