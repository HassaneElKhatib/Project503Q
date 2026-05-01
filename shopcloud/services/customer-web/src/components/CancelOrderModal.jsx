import { useEffect, useState } from "react";
import { MdClose } from "react-icons/md";

export default function CancelOrderModal({
  isOpen,
  onClose,
  onSubmit,
  orderId,
}) {
  const reasons = [
    "Ordered by mistake",
    "Found a better price",
    "Delivery is too slow",
    "Changed my mind",
    "Other",
  ];

  const [selectedReason, setSelectedReason] = useState("");
  const [customReason, setCustomReason] = useState("");

  useEffect(() => {
    if (!isOpen) {
      setSelectedReason("");
      setCustomReason("");
    }
  }, [isOpen]);

  const finalReason =
    selectedReason === "Other" ? customReason.trim() : selectedReason;

  const isDisabled = !finalReason;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-xl p-6 relative">

        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-black"
        >
          <MdClose size={22} />
        </button>

        <h2 className="text-xl font-bold text-gray-800 mb-2">
          Cancel Order
        </h2>

        <p className="text-sm text-gray-500 mb-4">
          Please select a reason for cancelling this order.
        </p>

        <div className="space-y-3">
          {reasons.map((reason) => (
            <label
              key={reason}
              className="flex items-center gap-3 cursor-pointer"
            >
              <input
                type="radio"
                name="cancelReason"
                value={reason}
                checked={selectedReason === reason}
                onChange={() => {
                  setSelectedReason(reason);
                  if (reason !== "Other") setCustomReason("");
                }}
              />
              <span className="text-gray-700">{reason}</span>
            </label>
          ))}
        </div>

        {selectedReason === "Other" && (
          <textarea
            className="w-full mt-4 border rounded-lg p-3 focus:outline-none focus:border-accent"
            placeholder="Please specify your reason"
            value={customReason}
            onChange={(e) => setCustomReason(e.target.value)}
          />
        )}

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 h-11 rounded-lg border border-gray-300 hover:bg-gray-100 transition cursor-pointer"
          >
            Back
          </button>

          <button
            disabled={isDisabled}
            onClick={() => onSubmit(orderId, finalReason)}
            className={`flex-1 h-11 rounded-lg text-white transition cursor-pointer
              ${
                isDisabled
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-red-500 hover:bg-red-600"
              }`}
          >
            Confirm Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
