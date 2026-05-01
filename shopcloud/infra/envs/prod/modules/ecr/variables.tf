variable "name_prefix" { type = string }

variable "repositories" {
  type = list(string)
  default = [
    "catalog",
    "auth",
    "cart",
    "admin",
    "checkout"
  ]
}
