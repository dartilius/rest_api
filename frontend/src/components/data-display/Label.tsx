interface LabelProps {
    children: React.ReactNode
    className?: string
  }
  
  export const Label = ({ children, className }: LabelProps) => (
    <div className={`text-3xl text-zinc-900 mb-1 ${className}`}>
      {children}
    </div>
  )