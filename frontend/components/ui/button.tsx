import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"

// shadcn Button, restyled to the BillBack palette: forest pill by default,
// coral for the one main action on a card, ghost for the quiet alternative.
const buttonVariants = cva(
  "inline-flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-full border-[1.5px] border-transparent px-6 py-3 text-[17px] leading-tight font-medium select-none transition-[transform,background-color,border-color] duration-150 ease-out active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-5",
  {
    variants: {
      variant: {
        default:
          "bg-ink text-card [@media(hover:hover)]:hover:bg-[color-mix(in_srgb,var(--ink)_88%,var(--card))]",
        coral:
          "bg-coral text-on-coral [@media(hover:hover)]:hover:bg-[color-mix(in_srgb,var(--coral)_90%,white)]",
        ghost:
          "border-line bg-transparent text-ink [@media(hover:hover)]:hover:border-ink [@media(hover:hover)]:hover:bg-[color-mix(in_srgb,var(--mint)_30%,transparent)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
