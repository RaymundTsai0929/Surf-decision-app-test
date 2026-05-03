interface Props {
  narrative: string | null
  loading: boolean
  error: string | null
  onFetch: () => void
}

export default function AIStory({ narrative, loading, error, onFetch }: Props) {
  if (loading) {
    return (
      <div className="w-full h-full p-3 flex flex-col gap-2">
        {[80, 100, 60, 90, 70].map((w, i) => (
          <div
            key={i}
            className="h-3 rounded bg-gray-700 animate-pulse"
            style={{ width: `${w}%` }}
          />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center p-4 gap-3">
        <p className="text-xs text-gray-500 text-center">敘述載入失敗</p>
        <button
          onClick={onFetch}
          className="text-xs text-blue-400 hover:text-blue-300 underline"
        >
          重試
        </button>
      </div>
    )
  }

  if (!narrative) {
    return (
      <div className="w-full h-full flex items-center justify-center p-4">
        <button
          onClick={onFetch}
          className="text-xs text-gray-500 hover:text-gray-300 text-center leading-relaxed transition-colors"
        >
          點此取得在地嚮導說明
        </button>
      </div>
    )
  }

  return (
    <div className="w-full h-full overflow-auto p-3">
      <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">{narrative}</p>
    </div>
  )
}
