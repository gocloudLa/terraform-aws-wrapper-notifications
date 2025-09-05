/*----------------------------------------------------------------------*/
/* Common |                                                             */
/*----------------------------------------------------------------------*/

# variable "metadata" {
#   type = any
# }

/*----------------------------------------------------------------------*/
/* RDS | Variable Definition                                            */
/*----------------------------------------------------------------------*/

variable "notifications_parameters" {
  description = ""
  type        = any
  default     = {}
}

variable "notifications_defaults" {
  description = ""
  type        = any
  default     = {}
}