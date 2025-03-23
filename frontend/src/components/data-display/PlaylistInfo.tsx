interface PlaylistInfoProps {
    playlist: {
      id: string
      name: string
      files_count: number
    }
    className?: string
  }
  
  export const PlaylistInfo = ({ playlist, className }: PlaylistInfoProps) => {
    return (
      <div className={`flex flex-col ${className}`}>
        <span className="font-semibold">{playlist.name}</span>
        <span className="text-xl text-zinc-900">
          {playlist.files_count} файлов • ID: {playlist.id}
        </span>
      </div>
    )
  }